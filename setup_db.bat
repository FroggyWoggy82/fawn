@echo off
echo Running migrations...
python manage.py migrate
echo Creating superuser...
python manage.py shell -c ^
"from django.contrib.auth.models import User; ^
if not User.objects.filter(username='steve').exists(): ^
    User.objects.create_superuser('steve', 'steve@example.com', 'Kevinhuy1'); ^
else: ^
    print('Superuser steve already exists.')"