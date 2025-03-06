from django.conf import settings
import os

def vapid_key(request):
    vapid_key = os.environ.get('VAPID_PUBLIC_KEY', '')
    if not vapid_key:
        print("Warning: VAPID_PUBLIC_KEY not found in environment variables")
    return {
        'vapid_public_key': vapid_key
    }