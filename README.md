plaintext
# PayPack

> AI 代理的通用支付中间件 —— 一行代码，让 AI 完成机器对机器的自动付款。

HTTP 402 状态码从 1991 年就存在于协议规范中，但三十年来从未被真正使用。原因很简单：当服务器返回“需要付款”时，屏幕前必须有一个人掏出信用卡。

AI 代理的出现改变了一切。一个自主运行的 AI 每小时可能发起数百次 API 调用、数据购买、内容订阅，金额小到 0.001 美元。传统支付体系在手续费和人工确认面前完全失效。

**x402 协议**（由 Coinbase 提出）和 **AP2 协议**（由 Google 提出）正在解决这个问题：服务器返回 402，附上收款地址和金额，AI 代理自动完成链上支付，整个过程在一次 HTTP 交互中完成，无需人类介入。

PayPack 的使命：做 AI 支付栈中最薄、最可靠、最不可绕过的**中间层**。

---

## 核心设计

```text
AI 代理应用
     │
     ▼
  PayPack SDK  ◄── 你在这里
     │
     ├── 协议解析层（x402 / AP2 / 更多）
     ├── 支付路由器（USDC 链上 / 法币通道）
     └── 安全熔断层（限额、审计、重试）
     │
     ▼
  底层结算网络（Solana / Base / 支付宝AI付 等）
PayPack 不发明新协议，而是把散落在各处的底层能力封装成一个 agent.pay()。

功能特性
多协议兼容：同时支持 x402 和 AP2，自动识别并切换

纳米支付优化：专为 0.01 美元以下交易设计，内置 Gas 费估算和批量结算

安全熔断：可设置日支出上限（单笔上限开发中）、收款地址白名单

完整审计日志：每一笔支付都有可查询的 JSON 收据

框架原生插件：LangChain / LlamaIndex 等主流 AI 框架的支付工具

双轨合规：同时对接海外稳定币通道（USDC）和国内合规通道（支付宝 AI 付）

LangChain 插件：已将支付能力封装为 LangChain Tool，可直接集成到 AI Agent 中（见 langchain_tool.py）

安装
bash
pip install https://gitee.com/rhcjw_com/paypack/raw/master/paypack-0.3.0-py3-none-any.whl
快速预览
https://gitee.com/rhcjw_com/paypack/raw/master/demo.gif

python
from paypack import AgentPay

# 初始化
pay = AgentPay(
    wallet_config={"private_key": "your-key"},
    network="base-sepolia",
    spend_limit_daily=10.0,
    broadcast=False
)

# 场景一：自动处理 HTTP 402
response = requests.get("https://api.data-provider.com/premium")
if response.status_code == 402:
    content = pay.auto_handle_402(response)

# 场景二：直接发起纳米支付
receipt = pay.send(
    to="0x接收地址",
    amount=0.001,
    currency="USDC"
)
print(receipt.tx_hash)
print(receipt.fee)
里程碑
✅ v0.1.0 (2026-06-20)
已在 Base Sepolia 测试网完成 ETH 和 USDC 双币种真实私钥签名交易，核心支付链路全部验证通过。

币种	金额	离线签名交易哈希
ETH	0.0001 ETH	d5f7ec94342c26a132289a9898ffd4885010089d1ddba19951117618a3992127
USDC	0.001 USDC	c4c24c4c1c8fd2ae738ed91cd87596ad2c672337b5ebf6d42a392adf61760e27
待网络环境恢复、测试币到位后，取消代码中广播注释即可立即上链。

✅ v0.3.0 (2026-06-21)
LangChain 工具插件测试通过，多链网络支持（Base/Polygon/Arbitrum 等主网就绪），支持环境变量私钥、余额检查。当钱包余额为 0 时，能准确触发 InsufficientFundsError 并提示“余额不足”，验证了安全检查链路的完整性。

路线图
阶段	目标	状态
v0.1	Base 测试网 x402 支付闭环（ETH + USDC）	✅ 已完成
v0.2	支持 AP2 协议解析	✅ 已完成
v0.3	LangChain 官方插件提交	✅ 已完成
v0.4	国内支付宝 AI 付通道对接	规划中
v1.0	云托管版本 PayPack Cloud	规划中
为什么是现在？
稳定币年交易量已突破 33 万亿美元（2025 年数据），是 PayPal 的 20 倍

AI 代理数量预计将达 220 亿个（麦肯锡）

x402 协议已在 Solana 上处理数千万笔交易

LangChain / LlamaIndex 支付插件市场目前完全空白

基础设施已经就绪，需求正在爆发。支付层缺一个标准答案。

参与进来
欢迎 Star 本仓库，提 Issue，或者直接联系我，如果你也在建设代理经济。

许可证
本项目采用 Apache License 2.0 开源。详见 LICENSE 文件。