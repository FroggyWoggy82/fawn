web: python manage.py migrate --fake && python manage.py collectstatic --noinput && gunicorn mealplanner.wsgi
worker: celery -A mealplanner worker -l info
beat: celery -A mealplanner beat -l info