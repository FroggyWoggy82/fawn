# Generated by Django 5.1.6 on 2025-03-01 23:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meals', '0005_exercise_workout_recipeingredient_recipetemplate_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='dailycaloriegoal',
            name='profile',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.CASCADE, to='meals.profile'),
        ),
        migrations.AddField(
            model_name='dailysubmission',
            name='profile',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.CASCADE, to='meals.profile'),
        ),
        migrations.AlterUniqueTogether(
            name='dailycaloriegoal',
            unique_together={('date', 'profile')},
        ),
    ]
