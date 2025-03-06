from django.core.management.base import BaseCommand
from django.utils import timezone
from meals.models import Notification

class Command(BaseCommand):
    help = 'Send scheduled notifications'

    def handle(self, *args, **options):
        now = timezone.now()
        notifications = Notification.objects.filter(
            enabled=True,
            next_send__lte=now
        )
        
        for notification in notifications:
            # Here you would implement the actual notification sending logic
            # This could be through email, push notifications, etc.
            self.stdout.write(f"Sending notification: {notification.title}")
            
            # Update last_sent and calculate next send time
            notification.last_sent = now
            notification.calculate_next_send()
            
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {notifications.count()} notifications'))