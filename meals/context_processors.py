import os

def vapid_key(request):
    return {
        'vapid_public_key': os.environ.get('VAPID_PUBLIC_KEY', '')
    }