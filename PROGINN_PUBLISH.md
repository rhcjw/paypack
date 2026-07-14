# PayPack 程序员客栈发布内容

> 打开 https://www.proginn.com/web/works_create 后逐项填写即可。

---

## 一、项目作品信息 — 选择分类

勾选：**✅ 开源项目**（技术语言框架、开源项目代码等）

---

## 二、名称（必填）

```
PayPack —— AI Agent 通用支付中间件
```

---

## 三、Vibe Coding 项目？

如果是复选框：**不勾选**（这是独立开发的正式开源项目，非纯 AI 生成）

---

## 四、语言技术（1-5个技术）— 下拉选择

以下是下拉菜单中应选的精准技术方向（选 5 个）：

| 优先级 | 建议选择 |
|--------|---------|
| 1 | **Python** |
| 2 | **LangChain**（或 AI框架 / LLM） |
| 3 | **Web3**（或 区块链） |
| 4 | **Solidity** |
| 5 | **Dify**（或 插件开发） |

> 备选：如果菜单中没有上面的，搜索：Node.js、React、TypeScript、Go、Rust、Java 等按实际代码栈选。核心是 **Python + LangChain + Web3**。

---

## 五、系统类型（1-3个类型）— 下拉选择

| 优先级 | 建议选择 |
|--------|---------|
| 1 | **SDK / 开发工具包** |
| 2 | **API 服务** |
| 3 | **中间件 / 插件** |

> 备选：工具软件、开源框架、支付系统

---

## 六、行业分类（1-2个行业）— 下拉选择

| 优先级 | 建议选择 |
|--------|---------|
| 1 | **人工智能** |
| 2 | **金融 / 支付** |

> 备选：区块链 / Web3、企业服务

---

## 七、行业场景（必填）— 最少40字，最多800字

> 📋 直接复制以下内容粘贴：

```
立项原因：AI Agent 时代到来，自主 AI 程序每小时可能调用上百次付费 API、订阅数据、购买服务，每笔金额可小至 0.001 美元。传统支付体系（信用卡、银行转账）有最低手续费门槛且需要人工审批，完全无法处理机器对机器的纳米支付。Coinbase 提出 x402 协议、Google 提出 AP2 协议来标准化机器支付，但市面上所有实现（Ampersend、GOAT、Stripe Agent Toolkit、Nevermined）都不支持支付宝和微信支付，中国 13 亿用户被排除在外。PayPack 填补了这一空白，是唯一同时支持 x402/AP2 链上支付（USDC/ETH）和支付宝/微信法币支付的 AI 支付中间件。

行业场景：面向 AI Agent 开发者生态，覆盖 Dify（数十万用户）、Coze/字节跳动（数百万用户）、百度千帆、通义百炼等低代码 AI 平台上的开发者。典型业务场景包括：AI 自动购买付费数据 API、Dify 聊天机器人内嵌付费咨询服务、Agent 与 Agent 之间的自动化经济结算。开发者用两行 Python 代码即可让 AI 具备支付能力，无需自己对接支付宝开放平台（几百页文档、RSA2 签名、沙箱调试）或管理链上钱包私钥。
```

---

## 八、功能介绍（必填）— 最多800字

> ⚠️ 注意：你之前填了 `https://www.proginn.com/` 占位符，请**清空后**粘贴以下内容：

```
1. x402/AP2 双协议解析：自动检测 HTTP 402 响应头，解析 Coinbase x402 和 Google AP2 协议的支付地址与金额，支持 AI 全自动处理付费 API 调用。

2. 多链加密货币支付：支持 ETH 和 USDC 在 Base、以太坊、Polygon、Arbitrum 四大链上的转账，已通过 Base Sepolia 测试网完成 ETH（0.0001 ETH）和 USDC（0.001 USDC）的真实链上交易验证。

3. 支付宝人民币支付：封装支付宝开放平台 RSA2 签名、page_pay 收银台、查单、退款等全部接口，沙箱环境已完成 0.63 元真实支付闭环（交易号 2026070922001406640510096995）。

4. ERC-4337 批量结算：基于账户抽象协议实现批量交易打包，显著降低多笔支付的 Gas 费用。

5. 安全机制：日消费限额持久化（SQLite/Redis）、支付前余额检查、AWS KMS 签名（生产环境私钥不出 HSM）、RPC 多节点故障自动转移、交易重试与 Replace-by-Fee。

6. 生态集成：LangChain 插件已发布 PyPI（pip install langchain-paypack），Dify 插件已提交官方插件市场（PR #2688），支持支付/查单/退款三合一。微信支付 JSAPI 后端已通（商业 License）。
```

---

## 九、项目实现（必填）— 最少40字，最多800字

> 📋 直接复制以下内容粘贴：

```
我负责了整个项目的全部开发工作，包括架构设计、代码编写、测试和文档撰写。

技术栈：Python 3.9+ 作为主开发语言，Web3.py 对接以太坊系区块链，Solidity 编写 ERC-4337 批量结算合约，LangChain 框架开发 AI Agent 工具插件，支付宝开放平台 SDK 集成 RSA2 签名与沙箱支付，AWS KMS 实现硬件安全模块签名，SQLite/Redis 做限额持久化存储。

架构亮点：采用签名器抽象层（Signer Abstraction），将 LocalSigner、AWSKMSSigner、AlipaySigner、WechatSigner 统一到同一接口下，AgentPay 主类不感知底层签名实现。RPC 故障转移层（FailoverProvider）支持多节点自动切换，确保链上交易不丢失。

实现难点：（1）支付宝 RSA2 签名需精确处理参数排序、URL 编码、SHA256WithRSA 签名和支付宝公钥验签，文档数百页，封装后仅需两行代码；（2）x402/AP2 双协议解析器需兼容 Coinbase 和 Google 两套不同的 HTTP 头规范，自动检测并路由；（3）ERC-4337 批量结算需理解 UserOperation 打包逻辑和 Bundler 端点交互。项目已通过 7 项离线测试和完整联网支付测试验证。
```

---

## 十、示例图片（最低2张）

请依次上传以下文件：

| 序号 | 文件路径 | 用途说明 |
|------|---------|---------|
| 1 | `C:\Users\Administrator\Desktop\paypack-new\demo.gif` | **链上支付全流程演示**（最重要，建议放第一张） |
| 2 | `C:\Users\Administrator\Desktop\paypack-new\zhihu_positioning.png` | **市场定位三圈图**（展示唯一性优势） |
| 3 | `C:\Users\Administrator\Desktop\paypack-new\zhihu_architecture.png` | **系统架构图** |
| 4 | `C:\Users\Administrator\Desktop\paypack-new\assets\paypack_sandbox_pay_qr.png` | **支付宝沙箱支付二维码**（法币支付验证） |
| 5 | `C:\Users\Administrator\Desktop\paypack-new\insufficient-funds-error.gif` | **安全机制：余额不足拦截演示** |

> 至少传 2 张，建议传 3-4 张。上传时用 PNG/GIF 格式。如果 GIF 太大，优先传静态 PNG。

---

## 快速检查清单

- [ ] 名称已填：`PayPack —— AI Agent 通用支付中间件`
- [ ] 分类已选：开源项目
- [ ] 技术已选 3-5 个（Python / LangChain / Web3）
- [ ] 行业场景已粘贴（约 280 字）
- [ ] 功能介绍已粘贴（约 400 字），⚠️ 清空原有的 `https://www.proginn.com/`
- [ ] 项目实现已粘贴（约 380 字）
- [ ] 至少 2 张截图已上传
- [ ] 检查无误 → 提交
