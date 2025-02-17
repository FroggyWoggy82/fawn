from django.contrib import admin
from .models import Ingredient, Dish, DishIngredient, DailySubmission, DailySubmissionIngredient

class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories_per_gram', 'protein_per_gram', 'fats_per_gram', 'carbohydrates_per_gram', 'cost_per_gram')
    search_fields = ('name',)

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'cook_time')
    search_fields = ('name',)
    inlines = [DishIngredientInline]

@admin.register(DishIngredient)
class DishIngredientAdmin(admin.ModelAdmin):
    list_display = ('dish', 'ingredient', 'default_quantity')
    search_fields = ('dish__name', 'ingredient__name')

@admin.register(DailySubmission)
class DailySubmissionAdmin(admin.ModelAdmin):
    list_display = ('dish', 'submission_date', 'total_calories', 'total_protein', 'total_fats', 'total_carbohydrates')
    search_fields = ('dish__name',)

@admin.register(DailySubmissionIngredient)
class DailySubmissionIngredientAdmin(admin.ModelAdmin):
    list_display = ('submission', 'dish_ingredient', 'grams_used')
    search_fields = ('submission__dish__name', 'dish_ingredient__ingredient__name')