from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64
import json


class Command(BaseCommand):
    help = 'Generate VAPID keys for Web Push notifications'

    def handle(self, *args, **kwargs):
        # Generate a private key for ECDH over NIST's P-256 curve
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        # Get the public key
        public_key = private_key.public_key()
        
        # Serialize the keys in the correct format for web push
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Extract the uncompressed point format for the public key (65 bytes: 0x04 + 32 bytes X + 32 bytes Y)
        public_numbers = public_key.public_numbers()
        public_bytes = b'\x04' + public_numbers.x.to_bytes(32, byteorder='big') + public_numbers.y.to_bytes(32, byteorder='big')
        
        # Convert to base64url format
        public_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
        
        # Save keys to a file for reference
        with open('vapid_keys.json', 'w') as f:
            json.dump({
                'public_key': public_b64,
                'private_key': private_pem.decode('utf-8'),
                'claims': {
                    'sub': 'mailto:your-email@example.com'
                }
            }, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS('VAPID keys generated successfully!'))
        self.stdout.write(self.style.NOTICE(f'Public Key: {public_b64}'))
        self.stdout.write(self.style.WARNING('Private Key (keep this secret): See vapid_keys.json file'))
        
        self.stdout.write('\n')
        self.stdout.write(self.style.SUCCESS('Keys have been saved to vapid_keys.json'))
        self.stdout.write(self.style.NOTICE('Next steps:'))
        self.stdout.write('1. Replace YOUR_VAPID_PUBLIC_KEY_HERE with the public key')
        self.stdout.write('2. Replace YOUR_VAPID_PRIVATE_KEY_HERE with the private key from the file')
        self.stdout.write('3. Update the email in VAPID_CLAIMS to your contact email')