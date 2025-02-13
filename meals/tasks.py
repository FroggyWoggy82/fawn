from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import DailySubmission
from django.utils import timezone
import logging
from meals.models import DailySubmission, Dish

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