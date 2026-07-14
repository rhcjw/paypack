# 知乎文章

---

**标题：我写了个开源项目，让 AI Agent 能付支付宝和微信——已提交 Dify 官方插件市场**

---

## 一、一个躺了 34 年的 HTTP 状态码

HTTP/1.0 规范（1991 年）定义了一个叫 `402 Payment Required` 的状态码。语义很直白：这个资源需要付费。

但 34 年来没人用过它。原因：服务器返回 402 的时候，需要一个人坐在屏幕前掏信用卡。自动化场景走不通。

**AI Agent 出现后变了。** 一个自主 AI 每小时可能调用上百次 API、买数据、订阅服务——单笔 $0.001。信用卡手续费吞掉交易，每笔要人工审批，结算周期以天计。

---

## 二、x402 和 AP2：机器支付的协议层

Coinbase 提了 **x402**，Google 提了 **AP2**。核心思路：服务器返回 402 时附带支付地址和金额，AI 自动完成链上转账——全程无人。

```
HTTP/1.1 402 Payment Required
X-402-Payee: 0xPayeeAddress
X-402-Amount: 0.001
X-402-Currency: USDC
```

但翻遍开源项目，全都不支持支付宝和微信：

| 工具 | 支付方式 | 中国用户？ |
|------|---------|-----------|
| Ampersend | x402 + USDC | ❌ |
| GOAT | 加密货币 | ❌ |
| Stripe Agent Toolkit | 信用卡 | ❌ |
| Nevermined | x402 | ❌ |
| **PayPack** | x402 + USDC/ETH + **支付宝 + 微信** | ✅ |

---

## 三、PayPack 是什么

**两行代码，让 AI Agent 付人民币。**

```python
from paypack.signer.alipay import AlipaySigner
from paypack import AgentPay

signer = AlipaySigner(app_id="你的APPID", private_key_path="私钥.pem",
                       alipay_public_key_path="支付宝公钥.pem", sandbox=True)
pay = AgentPay(signer=signer, network="alipay")

# AI 付人民币
pay.send(to="用户支付宝ID", amount=0.01, currency="CNY", subject="AI 订阅费")
```

链上支付同样简单——AI 自动处理 HTTP 402：

```python
response = requests.get("https://api.premium-weather.com/v2/tokyo")
if response.status_code == 402:
    pay.auto_handle_402(response)  # 自动付 0.001 USDC，继续干活
```

微信支付也跑通了：

```python
from paypack_wechat import WechatSigner

signer = WechatSigner(mchid="商户号", serial_no="证书序列号",
                       private_key_path="apiclient_key.pem",
                       api_v3_key="APIv3密钥", license_key="...",
                       app_id="小程序AppID")
pay = AgentPay(signer=signer, network="wechat")
# 后端下单 → 前端 wx.requestPayment() → 用户确认
```

---

## 四、Dify 插件 — 已提交官方市场

如果你用 Dify 搭 AI 应用，现在可以直接装支付插件了：

> Dify → 插件 → 从 GitHub 安装 → `https://github.com/rhcjw/paypack`

已提交 Dify 官方插件市场 PR [#2688](https://github.com/langgenius/dify-plugins/pull/2688)，审核通过后全 Dify 用户搜"支付"就能看到。

三个工具：**支付**（USDC/ETH/CNY 三币种）+ **查单** + **退款**。

---

## 五、项目状态（截至 2026.7.10）

| 通道 | 状态 |
|------|------|
| ETH/USDC 链上（Base/Ethereum/Polygon/Arbitrum） | ✅ 已跑通 |
| x402/AP2 协议解析 | ✅ 已实现 |
| 支付宝 CNY 沙箱 | ✅ 已通 |
| 微信支付 CNY | ✅ 后端已通（商业 License） |
| LangChain 插件 | ✅ PyPI 已发布 |
| Dify 插件 | ✅ PR #2688 审核中 |
| ERC-4337 批量结算 / RPC 故障转移 / 交易重试 | ✅ 已内置 |

安全机制：日消费限额、余额检查、AWS KMS 签名（生产环境私钥不出 HSM）——全部内置。

---

## 六、坐标图

```
x402/AP2 协议  →  Ampersend、Nevermined、PayPack
USDC/ETH 链上  →  GOAT、PayPack
支付宝/微信法币 →  PayPack（唯一）
```

**PayPack 是目前唯一同时覆盖三个圈的项目。** 国内 13 亿人用支付宝微信，不用 USDC——这个市场只有 PayPack 在做。

---

## 链接

- GitHub（中英双语）：https://github.com/rhcjw/paypack
- Gitee（国内更快）：https://gitee.com/rhcjw_com/paypack
- PyPI：`pip install langchain-paypack`
- 快速入门教程：https://github.com/rhcjw/paypack/blob/master/QUICKSTART.md
- Dify 插件 PR：https://github.com/langgenius/dify-plugins/pull/2688

---

**欢迎 star、试用、一起建设。如果你也希望 AI Agent 能付人民币的话。**
