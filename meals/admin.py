from django.contrib import admin
from .models import (Ingredient, Dish, DishIngredient, DailySubmission,
                    DailySubmissionIngredient, Profile, Exercise, Workout,
                    WorkoutExercise, ExerciseSet, WorkoutPreset, PresetExercise, HabitCompletion, Habit)

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

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Workout-related admin classes
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)

class ExerciseSetInline(admin.TabularInline):
    model = ExerciseSet
    extra = 1

@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ('workout', 'exercise', 'order')
    search_fields = ('exercise__name',)
    inlines = [ExerciseSetInline]

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'duration', 'preset', 'is_active')
    list_filter = ('start_time', 'preset')
    date_hierarchy = 'start_time'

@admin.register(ExerciseSet)
class ExerciseSetAdmin(admin.ModelAdmin):
    list_display = ('workout_exercise', 'set_number', 'weight', 'weight_unit', 'reps')
    list_filter = ('weight_unit',)
    search_fields = ('workout_exercise__exercise__name',)

class PresetExerciseInline(admin.TabularInline):
    model = PresetExercise
    extra = 1

@admin.register(WorkoutPreset)
class WorkoutPresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    inlines = [PresetExerciseInline]

@admin.register(PresetExercise)
class PresetExerciseAdmin(admin.ModelAdmin):
    list_display = ('preset', 'exercise', 'order')
    search_fields = ('preset__name', 'exercise__name')
    list_filter = ('preset',)

@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'frequency', 'created_at')
    list_filter = ('frequency',)
    search_fields = ('name', 'description')

@admin.register(HabitCompletion)
class HabitCompletionAdmin(admin.ModelAdmin):
    list_display = ('habit', 'completion_date', 'completed_at')
    list_filter = ('habit', 'completion_date')
    date_hierarchy = 'completion_date'

