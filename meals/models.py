from django.db import models
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


class WorkoutPreset(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
        
class PresetExercise(models.Model):
    preset = models.ForeignKey(WorkoutPreset, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey('Exercise', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    default_sets = models.PositiveIntegerField(default=3)
    min_reps = models.PositiveIntegerField(default=8)
    max_reps = models.PositiveIntegerField(default=12)
    custom_name = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        if self.custom_name:
            return f"{self.custom_name} in {self.preset.name}"
        return f"{self.exercise.name} in {self.preset.name}"
    
    def get_display_name(self):
        return self.custom_name if self.custom_name else self.exercise.name

class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ('back', 'Back'),
        ('arms', 'Arms'),
        ('chest', 'Chest'),
        ('shoulders', 'Shoulders'),
        ('core', 'Core'),
        ('legs', 'Legs'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    def __str__(self):
        return self.name

class Workout(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    preset = models.ForeignKey(WorkoutPreset, on_delete=models.SET_NULL, null=True, blank=True, related_name='workouts')
    
    def __str__(self):
        return f"Workout on {self.start_time.strftime('%Y-%m-%d')}"
    
    def is_active(self):
        return self.end_time is None
    
    def calculate_duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.exercise.name} for {self.workout}"
    
    def previous_workout_exercise(self):
        """Get the most recent previous workout exercise for the same exercise"""
        return WorkoutExercise.objects.filter(
            exercise=self.exercise,
            created_at__lt=self.created_at
        ).order_by('-created_at').first()

class ExerciseSet(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('lb', 'Pounds'),
    ]
    
    workout_exercise = models.ForeignKey(WorkoutExercise, on_delete=models.CASCADE, related_name='sets')
    set_number = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    weight_unit = models.CharField(max_length=2, choices=UNIT_CHOICES, default='lb')
    reps = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['set_number']
    
    def __str__(self):
        return f"Set {self.set_number}: {self.weight} {self.weight_unit} x {self.reps} reps"




class SkinProduct(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, blank=True)
    product_type = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.brand} {self.name}" if self.brand else self.name

class AcneEntry(models.Model):
    entry_date = models.DateField(default=timezone.now)
    severity = models.IntegerField(choices=[(1, "Clear"), (2, "Almost Clear"), 
                                           (3, "Mild"), (4, "Moderate"), 
                                           (5, "Severe")], default=3)
    image = models.ImageField(upload_to='acne_images/')
    notes = models.TextField(blank=True)
    products_used = models.ManyToManyField(SkinProduct, blank=True)
    
    class Meta:
        ordering = ['-entry_date']
        verbose_name_plural = "Acne Entries"
    
    def __str__(self):
        return f"Acne Entry on {self.entry_date}"




class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    calories_per_gram = models.FloatField(default=0)
    protein_per_gram = models.FloatField(default=0)
    fats_per_gram = models.FloatField(default=0)
    carbohydrates_per_gram = models.FloatField(default=0)
    cost_per_gram = models.FloatField(default=0)  # Existing per-gram field

    # New package fields for user input
    grams_in_package = models.FloatField(null=True, blank=True)
    calories_per_package = models.FloatField(null=True, blank=True)
    protein_per_package = models.FloatField(null=True, blank=True)
    fats_per_package = models.FloatField(null=True, blank=True)
    carbohydrates_per_package = models.FloatField(null=True, blank=True)
    cost_per_package = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # If package information is provided and grams_in_package is non-zero,
        # automatically calculate per-gram values.
        if self.grams_in_package and self.grams_in_package != 0:
            if self.calories_per_package is not None:
                self.calories_per_gram = self.calories_per_package / self.grams_in_package
            if self.protein_per_package is not None:
                self.protein_per_gram = self.protein_per_package / self.grams_in_package
            if self.fats_per_package is not None:
                self.fats_per_gram = self.fats_per_package / self.grams_in_package
            if self.carbohydrates_per_package is not None:
                self.carbohydrates_per_gram = self.carbohydrates_per_package / self.grams_in_package
            if self.cost_per_package is not None:
                self.cost_per_gram = self.cost_per_package / self.grams_in_package
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
class Dish(models.Model):
    name = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    cook_time = models.PositiveIntegerField(null=True, blank=True, help_text="Cook time in minutes")
    instructions = models.TextField(blank=True)
    ingredients = models.ManyToManyField(Ingredient, through='DishIngredient', related_name='dishes')

    def __str__(self):
        return self.name

class DishIngredient(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='dish_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    default_quantity = models.FloatField(null=True, blank=True, help_text="Default quantity in grams (optional)")

    def __str__(self):
        return f"{self.ingredient.name} for {self.dish.name}"

class DailySubmission(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    submission_date = models.DateField()
    notes = models.TextField()
   
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, null=True, blank=True, default=1)
    usage = models.ManyToManyField('Usage', blank=True)
    total_calories = models.IntegerField(default=0)
    total_protein = models.IntegerField(default=0)
    total_fats = models.IntegerField(default=0)
    total_carbohydrates = models.IntegerField(default=0)
    image = models.ImageField(upload_to='submissions/', blank=True, null=True)
    feeling_rating = models.IntegerField(choices=[(1, "Terrible"), (2, "Poor"), 
                                                 (3, "Okay"), (4, "Good"), 
                                                 (5, "Excellent")], default=3)

    def __str__(self):
        profile_name = self.profile.name if self.profile else "No Profile"
        return f"Submission on {self.submission_date} - {self.dish.name} ({profile_name})"
    
class Profile(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class WeightMeasurement(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateField()
    weight = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('profile', 'date')


class DailySubmissionIngredient(models.Model):
    submission = models.ForeignKey(DailySubmission, related_name='ingredients', on_delete=models.CASCADE)
    dish_ingredient = models.ForeignKey(DishIngredient, on_delete=models.CASCADE)
    grams_used = models.FloatField()
    cost_per_gram = models.FloatField(default=0)  # New field

    def __str__(self):
        return f"{self.grams_used}g of {self.dish_ingredient.ingredient.name}"

class Usage(models.Model):
    dish_ingredient = models.ForeignKey(DishIngredient, on_delete=models.CASCADE)
    grams_used = models.FloatField()


    
class DailyCalorieGoal(models.Model):
    date = models.DateField(unique=True)
    calorie_goal = models.PositiveIntegerField(default=0)
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, null=True, blank=True, default=1)
    
    class Meta:
        # Update unique constraint to include profile
        unique_together = ('date', 'profile')

    def __str__(self):
        profile_name = self.profile.name if self.profile else "No Profile"
        return f"{self.date}: {self.calorie_goal} ({profile_name})"
    
class Task(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)  # stored as a timedelta
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return self.title
    
class SubTask(models.Model):
    task = models.ForeignKey(Task, related_name="subtasks", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    parent = models.ForeignKey('self', related_name='nested_subtasks', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
class RecipeTemplate(models.Model):
    name = models.CharField(max_length=200)
    base_calories = models.FloatField()
    base_servings = models.FloatField(default=1)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(RecipeTemplate, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    base_quantity = models.FloatField()

class Habit(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, null=True, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class HabitCompletion(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateField()
    
    class Meta:
        # Ensure a habit can only be completed once per day
        unique_together = ('habit', 'completion_date')
        
    def __str__(self):
        return f"{self.habit.name} completed on {self.completion_date}"
    
# Add these models to models.py
class PushSubscription(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, null=True, blank=True)
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Push subscription for {self.profile.name if self.profile else 'unknown'}"

class NotificationSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    TYPE_CHOICES = [
        ('progress_picture', 'Progress Picture Reminder'),
        ('habit_reminder', 'Habit Reminder'),
        ('weight_reminder', 'Weight Tracking Reminder'),
    ]
    
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    day_of_week = models.IntegerField(null=True, blank=True)  # 0 = Monday, 6 = Sunday
    time_of_day = models.TimeField(default='09:00:00')
    last_sent = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.profile.name} ({self.get_frequency_display()})"


# Add these views to views.py


@require_POST
def subscribe_to_push(request):
    """API endpoint to subscribe for push notifications"""
    try:
        data = json.loads(request.body)
        subscription = data.get('subscription')
        notification_type = data.get('notification_type', 'progress_picture')
        frequency = data.get('frequency', 'weekly')
        
        # Get user profile
        profile = None
        if request.user.is_authenticated:
            profile = Profile.objects.filter(user=request.user).first()
        else:
            # If not authenticated, use the profile ID from the session or default to first profile
            profile_id = request.session.get('profile_id')
            if profile_id:
                profile = Profile.objects.filter(id=profile_id).first()
            
            if not profile:
                profile = Profile.objects.first()
        
        if not profile:
            return JsonResponse({'error': 'No profile found'}, status=400)
        
        # Save subscription
        push_subscription, created = PushSubscription.objects.update_or_create(
            endpoint=subscription.get('endpoint'),
            defaults={
                'profile': profile,
                'p256dh': subscription.get('keys', {}).get('p256dh', ''),
                'auth': subscription.get('keys', {}).get('auth', '')
            }
        )
        
        # Create notification schedule
        day_of_week = 0  # Monday by default
        if frequency == 'weekly':
            # Use Sunday (6) for weekly progress pictures by default
            day_of_week = 6
            
        notification_schedule, created = NotificationSchedule.objects.update_or_create(
            profile=profile,
            notification_type=notification_type,
            defaults={
                'frequency': frequency,
                'day_of_week': day_of_week,
                'active': True
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Successfully subscribed to {notification_type} notifications'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

