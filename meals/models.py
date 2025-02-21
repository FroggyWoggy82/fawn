from django.db import models
from django.utils import timezone

class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    calories_per_gram = models.FloatField(default=0)
    protein_per_gram = models.FloatField(default=0)
    fats_per_gram = models.FloatField(default=0)
    carbohydrates_per_gram = models.FloatField(default=0)
    cost_per_gram = models.FloatField(default=0)  # New field

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
