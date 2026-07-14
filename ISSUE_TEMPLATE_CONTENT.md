# LangChain 官方 Feature Request — PayPack Integration

> **在提交前，请打开此链接手动提交 Issue（不能用 API）：**
> https://github.com/langchain-ai/langchain/issues/new?template=feature-request.yml
>
> **然后复制下方内容填入对应字段。**

---

## 提交清单（勾选以下所有项）
- [x] 我已检查文档、API 参考和已有 issues，确认没有重复请求
- [x] 此请求是 LangChain 的新功能或增强，而非已有功能使用问题

## 功能请求描述

### 功能名称
将 `langchain-paypack` 列入 LangChain 官方社区集成（Community Integration / Tool）

### 功能简述
PayPack 是一个为 AI Agent 提供自主链上支付能力的 LangChain 工具，支持 x402（Coinbase）和 AP2（Google）协议的自动解析与支付执行，让 AI Agent 能在一次 HTTP 交互中完成"付款→获取数据"的闭环。

### 动机与价值（为什么 LangChain 用户需要这个？）

HTTP 402 "Payment Required" 状态码从 1991 年就存在于协议规范中，但三十年来从未真正被使用——因为服务器返回 402 时，必须有一个人掏出信用卡。AI Agent 的出现改变了这一局面：

- x402（Coinbase + Cloudflare）和 AP2（Google + 60+ 机构）正在将机器支付变为现实
- x402 已在 Base 链处理 1.19 亿笔交易，AP2 已提交 FIDO Alliance 标准化
- LangChain Agent 需要调用付费 API、订阅数据、购买算力时，目前没有统一的支付工具

PayPack 把这一切封装成 `agent.pay()`——一行代码解决问题。

### 建议的实现方式

发布为独立的 LangChain 社区包（`langchain-paypack`），遵循 LangChain 社区集成规范：

- **包名**: `langchain-paypack`（已发布 PyPI v0.5.0）
- **PyPI**: https://pypi.org/project/langchain-paypack/
- **代码仓库**: https://github.com/rhcjw/paypack

### 与现有功能的对比

| 方案 | x402 | AP2 | ERC-4337批量 | KMS签名 | RPC故障转移 |
|------|:--:|:--:|:--:|:--:|:--:|
| PayPack | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nevermined | ✅ | ✅ | ❌ | ❌ | ❌ |
| Coinbase facilitator | ✅ | ❌ | ❌ | ❌ | ❌ |

### 技术栈与兼容性

- **Python**: >= 3.10
- **依赖**: `langchain-core>=0.1.0`, `web3>=6.0.0`
- **支持链**: Base, Ethereum, Polygon, Arbitrum
- **许可证**: Apache 2.0
- **Stars**: 持续增长中
- **测试**: 完整离线测试套件（`test_offline.py`），GitHub Actions CI 配置完成
- **Demo**: Jupyter notebook 演示（`examples/agent_pays_api.ipynb`）
- **维护承诺**: 作者持续维护，Accepting PRs & Issues

### 代码示例

```python
# 安装
pip install langchain-paypack

# 在 LangChain Agent 中使用
from langchain_paypack import PayPackTool

tool = PayPackTool(
    private_key="0x...",
    network="base-sepolia",
    spend_limit_daily=10.0,
)

# Agent 调用支付
result = tool._run(to="0x...", amount=0.001, currency="USDC")
```

### 其他信息

- GitHub: https://github.com/rhcjw/paypack
- Demo notebook: https://github.com/rhcjw/paypack/blob/main/examples/agent_pays_api.ipynb
- 作者: ronghua (https://github.com/rhcjw)
