# Privacy Policy for PayPack Dify Plugin

**Last updated:** July 13, 2026

## Credential Handling

All sensitive materials are managed by Dify's secure credential vault system:

- **Signer Private Keys (ETH):** Stored in Dify built-in credential vault.
  Two operational modes are supported:
  - `LocalSigner`: Key resides in the vault and is loaded into memory only during transaction signing; never written to logs.
  - `AWSKMSSigner`: Key never leaves AWS HSM; the plugin sends signing requests to KMS.
- **Alipay Merchant Credentials** (App ID, RSA Private Key, Alipay Public Key): Stored in Dify credential vault; transmitted only via HTTPS to `openapi.alipay.com`.
- **WeChat Pay Credentials** (MchID, APIv3 Key, Serial Numbers, Certificate): Stored in Dify credential vault; transmitted only via HTTPS to `api.mch.weixin.qq.com`.
- **No credentials, transaction hashes, or merchant IDs are written to plugin execution logs.**

## Data Classification (Per Dify Guidelines)

| Category | Details |
|---|---|
| **Direct Identifiers** | None collected (no emails, usernames, phone, or contact info). |
| **Indirect Identifiers** | IP addresses (via network calls to facilitators/APIs), public transaction hashes (on-chain), and Merchant IDs. |
| **Combinable Data** | Agent tool-call context combined with a transaction hash could potentially be correlated. The plugin itself does not store these; Dify may log tool-call context per its own retention policies. |

## Data Not Collected

- No user prompts, message content, or PII.
- No on-chain data is persisted by the plugin (transaction hashes are inherently public on networks like Base/Ethereum).

## Local Sovereignty

This plugin operates in **local-signer mode** by design. All private keys, merchant credentials, and payment secrets are stored exclusively in Dify's Credential Vault on your own deployment. **No credentials are ever transmitted to any third-party cloud service.** The plugin makes outbound HTTPS calls only to the payment networks themselves (Alipay Open Platform, WeChat Pay API, Ethereum RPC endpoints). This design ensures full compatibility with enterprise private deployment requirements.

## Third-Party Services

The plugin communicates with:

- **x402 Facilitators (Coinbase default)** — Subject to facilitator privacy policy.
- **Alipay Open Platform** — Subject to Alipay privacy policy.
- **WeChat Pay** — Subject to WeChat Pay privacy policy.
- **Ethereum RPC endpoints** (Base, Ethereum, Polygon, Arbitrum) — Subject to respective node provider policies.

## Data Retention

- Payment order data is retained only as needed for transaction processing and reconciliation.
- Users can request data deletion by contacting the plugin author.

## Contact

For privacy-related questions: https://github.com/rhcjw
