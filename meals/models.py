from django.db import models
from django.utils import timezone

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
    # Change from CharField to ManyToManyField:
    usage = models.ManyToManyField('Usage', blank=True)
    total_calories = models.IntegerField(default=0)
    total_protein = models.IntegerField(default=0)
    total_fats = models.IntegerField(default=0)
    total_carbohydrates = models.IntegerField(default=0)
    image = models.ImageField(upload_to='submissions/', blank=True, null=True)

    def __str__(self):
        return f"Submission on {self.submission_date} - {self.dish.name}"


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

    def __str__(self):
        return f"{self.date}: {self.calorie_goal}"