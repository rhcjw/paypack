# 掘金/知乎技术文章草稿

---

**标题：如何让 AI Agent 拥有支付能力——PayPack 的设计与实践**

**副标题：从 HTTP 402 到支付宝，AI 自主支付的工程实现**

---

## 一、一个躺了 34 年的 HTTP 状态码

HTTP/1.0 规范（RFC 1945，1991 年）定义了一个叫做 `402 Payment Required` 的状态码。它的语义很直白：这个资源需要付费才能访问。

但 34 年来，几乎没有人用过它。

原因很朴素：服务器返回 402 的时候，需要一个人类坐在屏幕前，掏出信用卡，输入卡号，点"确认支付"。这个路径在自动化场景里完全走不通。

**直到 AI Agent 出现。**

一个自主运行的 AI Agent，每小时可能调用上百次 API、购买数据、订阅服务——单笔金额可能低至 $0.001。传统支付体系在这种场景下直接崩溃：
- 信用卡手续费吃掉交易
- 每笔都要人类审批
- 结算周期以天为单位

## 二、x402 和 AP2：机器支付的协议层

两个协议正在解决这个问题：

**x402**（Coinbase 提出）：当服务器返回 402 时，同时在响应头里附带支付方信息：
```
HTTP/1.1 402 Payment Required
X-402-Payee: 0xPayeeAddress
X-402-Amount: 0.001
X-402-Currency: USDC
X-402-Network: base
```

客户端解析这些头，完成链上转账，就能获取数据——全程不需要人类介入。

**AP2**（Google 提出）：理念类似，在协议层面定义了 AI Agent 之间的支付握手流程。

但问题来了：**协议有了，谁来实现？**

## 三、"别人都在搞"——但没人管中国用户

我翻遍了 AI 支付相关的开源项目：

| 工具 | 支付方式 | 中国用户？ | 定位 |
|------|---------|-----------|------|
| Ampersend | x402 + USDC | ❌ | x402 协议实现 |
| GOAT | 加密货币 | ❌ | AI Agent 框架 |
| Stripe Agent Toolkit | Stripe 信用卡 | ❌ 有限 | LangChain 插件 |
| Nevermined | x402 协议 | ❌ | 协议层 |
| Privy | 钱包基建 | ❌ | 嵌入式钱包 |
| **PayPack** | x402/AP2 + USDC/ETH + **支付宝** | ✅ **唯一** | **统一支付中间件** |

结论非常清楚：**所有人的注意力都在加密货币上，没人做支付宝/微信支付。**

这其实是巨大的市场空白。国内 13 亿人的支付习惯是支付宝和微信，不是 USDC。Dify 上有几十万开发者，Coze 上有几百万——这些平台全都没有支付工具。

## 四、PayPack 的设计思路

PayPack 的架构很简单：不发明新协议，而是把所有已有协议封装进一个统一接口。

```
       AI Agent Application
                │
                ▼
         PayPack SDK
                │
        ┌───────┼───────┐
        │       │       │
  Protocol   Payment   Security
   Parser    Router    Fuse
  (x402/    (USDC/    (Limits/
   AP2)     CNY)       Audit)
        │       │       │
        └───────┼───────┘
                │
                ▼
    Settlement Networks
  (Base / Alipay / ...)
```

核心设计决策：

### 1. Signer 抽象

不同支付通道有不同的签名方式。EVM 链用 ECDSA，支付宝用 RSA2，AWS 生产环境用 KMS。PayPack 把签名抽象成接口：

```python
# 开发环境：本地签名
signer = LocalSigner(private_key="0x...")

# 生产环境：KMS 签名（私钥不出 HSM）
signer = AWSKMSSigner(key_id="alias/paypack-eth-key")

# 支付宝：RSA2 签名
signer = AlipaySigner(app_id="xxx", private_key_path="key.pem",
                       alipay_public_key_path="alipay_pub.pem")
```

上层 `AgentPay` 不关心签名怎么做的，它只调 `signer.sign_transaction()`。

### 2. 协议自动路由

```python
response = requests.get("https://api.data-provider.com/premium")
if response.status_code == 402:
    content = pay.auto_handle_402(response)  # 自动检测 x402/AP2
```

`auto_handle_402` 解析响应头，自动识别 x402 还是 AP2，然后走对应的支付通道。

### 3. 双通道支付

```python
# 链上 USDC
pay.send(to="0x...", amount=0.001, currency="USDC")

# 支付宝人民币
pay.send(to="支付宝user_id", amount=9.90, currency="CNY",
         subject="AI API 月度订阅")
```

同一个 `pay.send()` 接口，后端根据 `currency` 走不同的结算网络。

## 五、工程实现细节

### 链上支付栈（v0.1-v0.5）

- **EVM 兼容**：Base / Ethereum / Polygon / Arbitrum
- **ERC-4337 批量结算**：多笔支付打包成单笔链上交易，节省 60-80% Gas
- **RPC 故障转移**：3 节点自动切换，避免单点故障
- **交易重试**：Replace-by-Fee + 指数退避
- **限额持久化**：Redis / SQLite / 内存，日限额可配置
- **AWS KMS 签名**：生产环境私钥永不出 HSM

### 支付宝集成（v0.6 开发中，沙箱已验证）

```python
class AlipaySigner(Signer):
    """
    支持:
    - alipay.trade.create（JSAPI/APP 支付）
    - alipay.trade.page.pay（电脑网站支付）
    - alipay.trade.query（交易查询）
    - alipay.trade.refund（退款）
    """
```

沙箱验证结果：
- RSA2 签名 ✅
- 支付订单创建 ✅
- 交易查询 ✅
- 沙箱交易号：`2026070922001406640510096995`

### 自己对接支付宝 vs 用 PayPack

| 步骤 | 自己对接 | PayPack |
|------|---------|------|
| 阅读支付宝开放平台文档 | 几百页 | 不需要 |
| 生成 RSA 密钥对 | 自己写脚本 | `generate_alipay_keys.py` |
| RSA2 签名实现 | ~50 行代码 | 内置 |
| 请求参数组装 | ~30 行代码 | 内置 |
| 验签回调处理 | ~80 行代码 | 内置 |
| API 调用封装 | ~100 行代码 | 内置 |
| **总计** | **几百行 + 几天调试** | **两行代码** |

## 六、PayPack 的定位

三个圈的交集：

```
  x402/AP2 协议支持  →  Ampersend、Nevermined、PayPack
  USDC/ETH 链上支付  →  GOAT、PayPack
  支付宝/微信法币支付 →  PayPack（唯一）
```

**PayPack 是唯一一个同时支持协议层、链上、法币三个维度的项目。**

这不是"意义很小"，这是"国内 AI 开发者目前唯一的选择"。

## 七、谁在用？

- **Dify 用户**（数十万）：想在 Dify 工作流里加上支付节点？目前只能自己写代码。PayPack 可以成为 Dify 插件。
- **Coze 用户**（数百万）：Coze Bot 想卖服务收钱？没这个能力。PayPack 可以填补。
- **百度千帆 / 通义百炼**：同理。

这些平台的开发者不看 LangChain 官方文档，他们看的是中文教程、B 站视频、掘金文章。

## 八、开源和路线图

- GitHub: https://github.com/rhcjw/paypack
- Gitee: https://gitee.com/rhcjw_com/paypack
- PyPI: `pip install langchain-paypack`

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.5 | 链上支付 + LangChain + 故障转移 + 重试 | ✅ |
| v0.6 | 支付宝生产环境 | 🚧 |
| v1.0 | PayPack Cloud 托管服务 | 🚧 |

---

**如果你也希望 AI Agent 能付人民币，欢迎 star、试用、一起建设。**
