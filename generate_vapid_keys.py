#!/usr/bin/env python
"""
Script to generate VAPID keys for Web Push notifications.
"""
import os
import json
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    """
    Generate a public/private key pair suitable for VAPID.
    
    Returns:
        dict: A dictionary with public_key and private_key.
    """
    # Generate a new EC key pair using the P-256 curve (as required by the Web Push standard)
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Get the public key in compressed format
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint
    )
    
    # Get the private key in DER format
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Convert to URL-safe base64
    public_key_base64 = base64.urlsafe_b64encode(public_key).decode('utf-8').rstrip('=')
    private_key_base64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')
    
    return {
        'public_key': public_key_base64,
        'private_key': private_key_base64
    }

def save_keys_to_file(keys, filename='.vapid_keys.json'):
    """
    Save the VAPID keys to a JSON file.
    
    Args:
        keys (dict): Dictionary containing public_key and private_key.
        filename (str): Path to save the keys.
    """
    with open(filename, 'w') as f:
        json.dump(keys, f)
    
    # Set appropriate file permissions (readable only by owner)
    os.chmod(filename, 0o600)
    
    print(f"VAPID keys saved to {filename}")
    print(f"Public key: {keys['public_key']}")
    print(f"Private key: {keys['private_key']}")

def load_keys_from_file(filename='.vapid_keys.json'):
    """
    Load VAPID keys from a JSON file.
    
    Args:
        filename (str): Path to the keys file.
        
    Returns:
        dict: Dictionary containing public_key and private_key.
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

if __name__ == "__main__":
    # Check if keys already exist
    keys_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.vapid_keys.json')
    keys = load_keys_from_file(keys_file)
    
    if keys:
        print("VAPID keys already exist:")
        print(f"Public key: {keys['public_key']}")
        print(f"Private key: {keys['private_key']}")
        
        regenerate = input("Do you want to regenerate the keys? (y/n): ").lower()
        if regenerate != 'y':
            print("Keeping existing keys.")
            exit(0)
    
    # Generate new keys
    print("Generating new VAPID keys...")
    keys = generate_vapid_keys()
    save_keys_to_file(keys, keys_file)
    
    print("\nAdd these keys to your Django settings.py:")
    print(f"VAPID_PRIVATE_KEY = '{keys['private_key']}'")
    print(f"VAPID_PUBLIC_KEY = '{keys['public_key']}'")
    print(f"VAPID_ADMIN_EMAIL = 'mailto:your-email@example.com'  # Replace with your email")