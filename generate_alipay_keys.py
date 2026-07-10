"""Generate RSA key pair for Alipay Open Platform integration."""
from Crypto.PublicKey import RSA
import os

key_dir = os.path.join(os.path.dirname(__file__), 'paypack', 'signer', 'keys')
os.makedirs(key_dir, exist_ok=True)

# Generate 2048-bit RSA key pair
key = RSA.generate(2048)

# Save private key (PKCS#1)
private_pem = key.export_key(format='PEM').decode()
with open(os.path.join(key_dir, 'alipay_private_key.pem'), 'w') as f:
    f.write(private_pem)

# Save public key (PKCS#8)
public_pem = key.publickey().export_key(format='PEM').decode()
with open(os.path.join(key_dir, 'alipay_public_key.pem'), 'w') as f:
    f.write(public_pem)

# Stripped public key for Alipay upload
public_key_stripped = (public_pem
    .replace('-----BEGIN PUBLIC KEY-----', '')
    .replace('-----END PUBLIC KEY-----', '')
    .replace('\n', '').strip())
with open(os.path.join(key_dir, 'alipay_public_key_upload.txt'), 'w') as f:
    f.write(public_key_stripped)

print("Keys generated in:", key_dir)
print("\n=== Public Key (paste into Alipay Open Platform) ===")
print(public_key_stripped)
print(f"\nTotal length: {len(public_key_stripped)} chars")
print("\n=== Private Key (keep secret!) ===")
print(private_pem[:80] + "...[truncated]")
