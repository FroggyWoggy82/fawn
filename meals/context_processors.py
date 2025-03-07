def vapid_key(request):
    vapid_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
    if not vapid_key:
        print("Warning: VAPID_PUBLIC_KEY not found in settings")
    return {
        'vapid_public_key': vapid_key
    }