# Generated by Django 5.1.6 on 2025-03-15 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meals', '0017_alter_task_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='habit',
            name='completion_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
