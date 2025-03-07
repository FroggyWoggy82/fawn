from django.conf import settings

def vapid_key(request):
    try:
        vapid_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
        return {'vapid_public_key': vapid_key}
    except Exception as e:
        # Log the error but don't crash
        print(f"Error in vapid_key context processor: {e}")
        return {'vapid_public_key': ''}