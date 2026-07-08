"""
交易重试机制。
支持 nonce 冲突恢复、Replace-by-Fee、可配置重试策略。
"""

import time
from typing import Callable, Optional
from dataclasses import dataclass, field


@dataclass
class RetryConfig:
    """交易重试配置"""

    max_retries: int = 3
    """最大重试次数"""

    retry_delay: float = 1.0
    """初始重试等待（秒），每次重试后翻倍（指数退避）"""

    rbf_gas_bump: float = 0.15
    """Replace-by-Fee Gas 提价比例（15%）"""

    tx_timeout: int = 120
    """交易确认超时（秒）"""

    retryable_rpc_errors: tuple = field(default=(
        "timeout",
        "connection",
        "503",
        "502",
        "504",
        "429",
        "too many requests",
        "rate limit",
    ))
    """可重试的 RPC 错误关键词（不区分大小写）"""


def is_retryable_rpc_error(error: Exception, config: RetryConfig) -> bool:
    """判断 RPC 错误是否可重试"""
    msg = str(error).lower()
    return any(keyword in msg for keyword in config.retryable_rpc_errors)


def is_nonce_error(error: Exception) -> bool:
    """判断是否是 nonce 冲突错误"""
    msg = str(error).lower()
    return any(kw in msg for kw in ["nonce too low", "nonce already", "replacement transaction underpriced"])


def broadcast_with_retry(
    send_fn: Callable[[], bytes],
    wait_fn: Callable[[bytes], dict],
    get_nonce_fn: Callable[[], int],
    config: Optional[RetryConfig] = None,
) -> dict:
    """
    带重试的交易广播。

    Args:
        send_fn: 发送签名交易的函数，返回 tx_hash
        wait_fn: 等待交易收据的函数，接收 tx_hash，返回 receipt
        get_nonce_fn: 获取当前 nonce 的函数
        config: 重试配置

    Returns:
        交易收据 dict

    Raises:
        RuntimeError: 超过最大重试次数仍失败
    """
    cfg = config or RetryConfig()
    last_error = None
    delay = cfg.retry_delay

    for attempt in range(cfg.max_retries + 1):
        try:
            tx_hash = send_fn()

            # 等待确认
            try:
                receipt = wait_fn(tx_hash, timeout=cfg.tx_timeout)
                return {
                    "tx_hash": tx_hash.hex() if isinstance(tx_hash, bytes) else tx_hash,
                    "block_number": receipt.get("blockNumber"),
                    "status": "success" if receipt.get("status") == 1 else "failed",
                    "attempts": attempt + 1,
                }
            except Exception as e:
                if is_nonce_error(e):
                    # nonce 冲突：重新获取 nonce 并重试
                    raise
                # 交易卡住（pending 过久）：RBF 提速
                if attempt < cfg.max_retries:
                    # 这里由调用方实现 RBF 逻辑
                    raise RuntimeError(f"交易在 {cfg.tx_timeout}s 内未确认，尝试 RBF 重发") from e
                raise

        except Exception as e:
            last_error = e
            if is_nonce_error(e) or "RBF" in str(e):
                # 刷新 nonce
                try:
                    get_nonce_fn()
                except Exception:
                    pass

            if attempt < cfg.max_retries and is_retryable_rpc_error(e, cfg):
                time.sleep(delay)
                delay *= 2  # 指数退避
                continue
            elif attempt < cfg.max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            break

    raise RuntimeError(
        f"交易广播失败，已重试 {cfg.max_retries} 次。最后错误: {last_error}"
    )


def rbf_resend(
    build_txn_fn: Callable[[float], dict],
    sign_fn: Callable[[dict], object],
    send_fn: Callable[[object], bytes],
    original_gas_price: int,
    bump: float = 0.15,
) -> bytes:
    """
    Replace-by-Fee：用更高 Gas 费重发交易。

    Args:
        build_txn_fn: 构建交易函数，接收 gas_price_multiplier
        sign_fn: 签名函数
        send_fn: 发送函数
        original_gas_price: 原交易的 gasPrice 或 maxFeePerGas
        bump: 提价比例（默认 15%）

    Returns:
        新交易的 tx_hash
    """
    new_gas = int(original_gas_price * (1 + bump))
    txn = build_txn_fn(new_gas)
    signed = sign_fn(txn)
    return send_fn(signed.raw_transaction)
