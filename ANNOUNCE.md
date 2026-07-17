# PayPack Cloud 开发者控制台已上线 🚀

**让 AI Agent 在任意网站上自主支付。**

## 三步接入

### 1. 注册拿 Key
打开 [rhcjw.com/pay/dashboard](https://rhcjw.com/pay/dashboard)
→ 输入用户名和邮箱
→ 秒获 API Key（ppk_xxx...）

### 2. 充值
支付宝/微信扫码充值
→ 余额即时到账
→ 每次 API 调用仅扣 1 分钱

### 3. 跑起来
```bash
pip install langchain-paypack
```

```python
from paypack import AgentPay

pay = AgentPay(
    wallet_config={"private_key": "0x你的私钥"},
    network="base-sepolia",
    spend_limit_daily=10.0,
)

receipt = pay.send(to="0x收款地址", amount=0.001, currency="ETH")
print(receipt["tx_hash"])
```

## 支持

- 💰 支付宝 / 微信支付 / ETH / USDC
- 🤖 Dify 插件 / LangChain 集成
- 🌐 任意网站浏览器自主支付 (agent.py)
- 👁️ Qwen-VL 视觉识别

控制台：[rhcjw.com/pay/dashboard](https://rhcjw.com/pay/dashboard)
GitHub：[github.com/rhcjw/paypack](https://github.com/rhcjw/paypack)
PyPI：[pypi.org/project/langchain-paypack](https://pypi.org/project/langchain-paypack/)
