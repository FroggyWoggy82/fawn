from pywebpush import webpush, WebPushException
import os
import base64

# Generate VAPID keys
vapid_private_key = os.urandom(32)
vapid_public_key = os.urandom(65)  # P-256 public key is 65 bytes

# Convert to base64
vapid_private_key_b64 = base64.urlsafe_b64encode(vapid_private_key).decode('utf-8')
vapid_public_key_b64 = base64.urlsafe_b64encode(vapid_public_key).decode('utf-8')

print("VAPID_PUBLIC_KEY=" + vapid_public_key_b64)
print("VAPID_PRIVATE_KEY=" + vapid_private_key_b64)