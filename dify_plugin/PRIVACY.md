# Privacy Policy for PayPack Dify Plugin

**Last updated:** July 10, 2026

## Data Collection

The PayPack Dify Plugin does **not** collect, store, or transmit any personal data directly.

## Credential Handling

- API keys and merchant credentials are stored securely in Dify's built-in credential vault (encrypted at rest).
- Credentials are only used to authenticate API calls to external payment services (Alipay, WeChat Pay, blockchain RPC endpoints).
- No credentials are logged, cached, or transmitted to any third party beyond the intended payment provider.

## Third-Party Services

The plugin communicates with:

- **PayPack Cloud API** (for cloud-based payment processing)
- **Alipay OpenAPI** (for Alipay payments)
- **WeChat Pay API** (for WeChat Pay payments)
- **Ethereum RPC endpoints** (for USDC/ETH on-chain payments)

Each third-party service has its own privacy policy. Users should review those policies independently.

## Data Retention

- Payment order data is retained only as needed for transaction processing and reconciliation.
- Users can delete their data by contacting the plugin author.

## Contact

For privacy-related questions, contact: https://github.com/rhcjw
