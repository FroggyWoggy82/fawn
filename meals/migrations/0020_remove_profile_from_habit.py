# Generated by Django 5.1.6 on 2025-03-15 18:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('meals', '0019_alter_habit_frequency'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='habit',
            name='profile',
        ),
    ]
