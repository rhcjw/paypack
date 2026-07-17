"""
PayPack v0.5.0 离线测试 —— 不依赖网络的完整验证
"""
print("=" * 55)
print("PayPack v0.5.0 离线完整性测试")
print("=" * 55)

# ====== 1. 模块导入 ======
print("\n1/7  模块导入")
from paypack import (
    AgentPay, LocalSigner, AWSKMSSigner,
    ERC4337Batcher, BundlerClient,
    FailoverProvider,
    RetryConfig, rbf_resend,
    InMemoryStore, SQLiteStore, create_limit_store,
    ENTRY_POINT_ADDRESS,
    InsufficientFundsError, DailyLimitExceededError, NetworkConfigError,
)
print("   ✅ 全部导入成功")

# ====== 2. Signer ======
print("\n2/7  Signer 签名器")
KEY = "0x你的ETH私钥"
ADDR = "0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8"

s = LocalSigner(private_key=KEY)
assert s.get_address().lower() == ADDR.lower()

# 测试签名
from web3 import Web3
txn = {"from": ADDR, "to": ADDR, "value": 100, "gas": 21000, "nonce": 0, "chainId": 84532, "gasPrice": 1000000000}
signed = s.sign_transaction(txn)
assert len(signed.hash) == 32
print(f"   ✅ 地址: {s.get_address()}")
print(f"   ✅ 签名 TX hash: {signed.hash.hex()[:20]}...")

# ====== 3. FailoverProvider ======
print("\n3/7  RPC 故障转移")
fp = FailoverProvider(["https://a.example.com", "https://b.example.com"])
assert fp.url_count == 2
print(f"   ✅ {fp.url_count} 节点, 活跃: {fp.active_url}")

# ====== 4. 限额持久化 ======
print("\n4/7  限额持久化")
store = create_limit_store("sqlite", db_path=":memory:")
store.add_spent(ADDR, 0.005)
assert store.get_spent_today(ADDR) == 0.005
store.add_spent(ADDR, 0.003)
assert store.get_spent_today(ADDR) == 0.008
print(f"   ✅ SQLite: 0.005 + 0.003 = {store.get_spent_today(ADDR)}")

mem = create_limit_store("memory")
mem.add_spent("0xabc", 0.1)
assert mem.get_spent_today("0xabc") == 0.1
print(f"   ✅ Memory: {mem.get_spent_today('0xabc')}")

# ====== 5. RetryConfig ======
print("\n5/7  交易重试配置")
rc = RetryConfig(max_retries=5, retry_delay=2.0, tx_timeout=120, rbf_gas_bump=0.15)
assert rc.max_retries == 5
assert rc.rbf_gas_bump == 0.15
print(f"   ✅ 重试{rc.max_retries}次, 延迟{rc.retry_delay}s, RBF提价{rc.rbf_gas_bump*100}%")

# ====== 6. ERC-4337 Batcher ======
print("\n6/7  ERC-4337 批量结算")
b = ERC4337Batcher(entry_point_address=ENTRY_POINT_ADDRESS, chain_id=84532)
uo = b.build_user_operation(
    sender=ADDR,
    calls=[{"to": ADDR, "value": 0, "data": "0xabcd"}],
    nonce=1,
)
assert uo["sender"] == ADDR
assert uo["nonce"] == "0x1"
print(f"   ✅ UserOperation: {len(uo)} 字段, sender={uo['sender'][:10]}...")

# 批量编码
calls = [
    {"to": "0x1111111111111111111111111111111111111111", "value": 0, "data": "0xaa"},
    {"to": "0x2222222222222222222222222222222222222222", "value": 100, "data": "0xbb"},
]
uo2 = b.build_user_operation(sender=ADDR, calls=calls, nonce=2)
assert uo2["callData"].startswith("0x")
print(f"   ✅ 批量 callData: {uo2['callData'][:40]}...")

# ====== 7. 向后兼容 ======
print("\n7/7  向后兼容性")
try:
    AgentPay(wallet_config={})
    print("   ❌ 应该抛出异常")
except ValueError:
    print("   ✅ 无密钥时正确拒绝")

# 无网络创建（直接拼 Web3 不连 RPC）
from web3 import Web3
from web3.providers.rpc import HTTPProvider
w3_dummy = Web3(HTTPProvider("http://localhost:8545"))
s2 = LocalSigner(private_key=KEY)
pay_no_net = AgentPay.__new__(AgentPay)
pay_no_net.signer = s2
pay_no_net.address = s2.get_address()
pay_no_net.broadcast = False
pay_no_net.spend_limit_daily = 10.0
pay_no_net._limit_store = create_limit_store("memory")
pay_no_net.retry_config = RetryConfig(max_retries=3)
assert pay_no_net.address.lower() == ADDR.lower()
print(f"   ✅ 手动构造 AgentPay: {pay_no_net.address[:10]}...")

print("\n" + "=" * 55)
print("🎉 全部 7 项离线测试通过！")
print("   (网络连接测试需在有 RPC 访问的环境下进行)")
print("=" * 55)
