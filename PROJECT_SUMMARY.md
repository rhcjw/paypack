# PayPack 项目速览（2026-07-08）

## 项目定位
AI Agent 通用支付中间件。HTTP 402 / x402 / AP2 协议，ETH/USDC 链上支付，LangChain 插件。

## 当前版本: v0.5.0

## 代码结构
```
paypack/
├── core.py              # AgentPay 主类
├── signer/              # 签名器（LocalSigner + AWSKMSSigner）
├── nanopay/             # ERC-4337 批量结算（Batcher + Bundler）
├── providers.py         # RPC 故障转移（FailoverProvider）
├── retry.py             # 交易重试（RBF + 指数退避）
├── limits.py            # 限额持久化（Redis/SQLite/内存）
└── __init__.py
langchain_paypack/       # LangChain 插件包
├── __init__.py
└── tools.py             # PayPackTool
```

## 发布渠道
- PyPI: https://pypi.org/project/langchain-paypack/
- GitHub: https://github.com/rhcjw/paypack (main 分支)
- Gitee: https://gitee.com/rhcjw_com/paypack (master 分支)
- npm install: pip install langchain-paypack

## 提交的 PR/Issue
- Awesome LangChain PR: https://github.com/kyrolabs/awesome-langchain/pull/448
- LangChain 官方 Issue: https://github.com/langchain-ai/langchain/issues/38725

## 测试
- test_offline.py — 离线 7 项测试全部通过
- test_industrial.py — 联网测试（需 RPC 可访问）
- 当前网络 sepolia.base.org SSL 握手超时

## 下一步计划
- v0.6: 支付宝 AI 付通道
- v1.0: PayPack Cloud
- 申请 Base Grants + Gitcoin
- 等 Awesome LangChain PR 合并
