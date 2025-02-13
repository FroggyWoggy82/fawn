from django.contrib import admin
from .models import Ingredient, Dish, DishIngredient, DailySubmission, DailySubmissionIngredient

class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1  # Number of extra forms to display

class DishAdmin(admin.ModelAdmin):
    inlines = [DishIngredientInline]

admin.site.register(Ingredient)
admin.site.register(Dish, DishAdmin)
admin.site.register(DishIngredient)
admin.site.register(DailySubmission)
admin.site.register(DailySubmissionIngredient)