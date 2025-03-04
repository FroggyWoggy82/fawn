from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import DailySubmission, NotificationSchedule, PushSubscription
from django.utils import timezone
import logging
import requests
import json
from meals.models import DailySubmission, Dish
from django.core.management import call_command
from pywebpush import webpush, WebPushException
from datetime import timedelta

logger = logging.getLogger(__name__)

@shared_task
def send_daily_submission_email():
    logger.info("Starting send_daily_submission_email task")
    try:
        submissions = DailySubmission.objects.filter(submission_date=timezone.now().date())
        if submissions.exists():
            logger.info(f"Found {submissions.count()} submissions")
            subject = 'Daily Meal Submissions'
            html_message = render_to_string('meals/daily_submission_email.html', {'submissions': submissions})
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            to = 'kevinguyen022@gmail.com'  # Change this to the desired recipient email address

            send_mail(subject, plain_message, from_email, [to], html_message=html_message)
            logger.info("Email sent successfully")
        else:
            logger.info("No submissions found")
    except Exception as e:
        logger.error(f"Error in send_daily_submission_email task: {e}")

@shared_task
def simple_task():
    logger.info("Starting simple_task")
    try:
        # Simplified task for testing
        logger.info("Simple task executed successfully")
    except Exception as e:
        logger.error(f"Error in simple_task: {e}")

# Assuming you have a Dish object already created
dish = Dish.objects.first()

# Create a DailySubmission object with the current date
submission = DailySubmission.objects.create(
    dish=dish,
    submission_date=timezone.now().date(),
    notes="Test submission",
    total_calories=500,
    total_protein=30,
    total_fats=20,
    total_carbohydrates=50
)

# Verify that the submission was created
print(DailySubmission.objects.filter(submission_date=timezone.now().date()).count())


@shared_task
def check_service_schedule():
    call_command('schedule_service')

# VAPID keys loaded from vapid_keys.json
import json
import os

# Load VAPID keys from the JSON file
vapid_keys_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'vapid_keys.json')
with open(vapid_keys_path, 'r') as f:
    vapid_keys = json.load(f)

VAPID_PRIVATE_KEY = vapid_keys['private_key']
VAPID_PUBLIC_KEY = vapid_keys['public_key']
VAPID_CLAIMS = vapid_keys['claims']

@shared_task
def send_scheduled_notifications():
    """Task to send all scheduled notifications"""
    now = timezone.now()
    today_weekday = now.weekday()  # 0 = Monday, 6 = Sunday
    
    # Get all active notification schedules for today's weekday
    schedules = NotificationSchedule.objects.filter(
        active=True,
        day_of_week=today_weekday
    )
    
    for schedule in schedules:
        # For weekly notifications, check if it's been at least 6 days since last notification
        if schedule.frequency == 'weekly':
            if schedule.last_sent and (now - schedule.last_sent) < timedelta(days=6):
                continue
                
        # For monthly notifications, check if it's been at least 28 days
        elif schedule.frequency == 'monthly':
            if schedule.last_sent and (now - schedule.last_sent) < timedelta(days=28):
                continue
                
        # For daily notifications, check if we already sent one today
        elif schedule.frequency == 'daily':
            if schedule.last_sent and schedule.last_sent.date() == now.date():
                continue
        
        # Get notification content based on type
        notification_data = get_notification_data(schedule)
        
        # Get all subscriptions for this profile
        subscriptions = PushSubscription.objects.filter(profile=schedule.profile)
        
        sent_count = 0
        for subscription in subscriptions:
            success = send_push_notification(subscription, notification_data)
            if success:
                sent_count += 1
        
        if sent_count > 0:
            # Update last_sent time
            schedule.last_sent = now
            schedule.save()
    
    return True

def get_notification_data(schedule):
    """Generate notification content based on schedule type"""
    notification_type = schedule.notification_type
    profile_name = schedule.profile.name
    
    if notification_type == 'progress_picture':
        return {
            'title': 'Progress Picture Reminder',
            'body': f"Hey {profile_name}! It's time to take your weekly progress picture.",
            'url': '/acne/new/',  # Redirect to the acne entry form
            'actions': [
                {
                    'action': 'take_picture',
                    'title': 'Take Picture'
                },
                {
                    'action': 'dismiss',
                    'title': 'Dismiss'
                }
            ]
        }
    elif notification_type == 'habit_reminder':
        # Get incomplete habits for today
        from .models import Habit, HabitCompletion
        today = timezone.now().date()
        
        # Get habits that haven't been completed today
        habits = Habit.objects.filter(profile=schedule.profile)
        incomplete_count = 0
        
        for habit in habits:
            if not HabitCompletion.objects.filter(habit=habit, completion_date=today).exists():
                incomplete_count += 1
        
        if incomplete_count == 0:
            return None  # No incomplete habits, don't send notification
            
        return {
            'title': 'Habit Reminder',
            'body': f"You have {incomplete_count} incomplete habits today. Don't break your streak!",
            'url': '/habits/',
            'actions': [
                {
                    'action': 'view_habits',
                    'title': 'View Habits'
                }
            ]
        }
    elif notification_type == 'weight_reminder':
        return {
            'title': 'Weight Tracking Reminder',
            'body': f"Time to log your weight for this week, {profile_name}!",
            'url': '/dashboard/',
            'actions': [
                {
                    'action': 'log_weight',
                    'title': 'Log Weight'
                }
            ]
        }
    
    # Default fallback
    return {
        'title': 'Reminder',
        'body': f"Don't forget to check your health tracking app!",
        'url': '/'
    }

def send_push_notification(subscription, notification_data):
    """Send a push notification to a specific subscription"""
    if not notification_data:
        return False
        
    try:
        subscription_info = {
            'endpoint': subscription.endpoint,
            'keys': {
                'p256dh': subscription.p256dh,
                'auth': subscription.auth
            }
        }
        
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(notification_data),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        
        return True
    except WebPushException as e:
        # Handle expired subscriptions
        if e.response and e.response.status_code == 410:
            # Subscription expired or was deleted
            subscription.delete()
        
        print(f"Push notification error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error sending notification: {str(e)}")
        return False