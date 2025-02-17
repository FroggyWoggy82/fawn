from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .forms import DailySubmissionForm, DishForm
from .models import DailySubmission, DishIngredient, DailySubmissionIngredient, Dish, Ingredient

def home_view(request):
    return render(request, 'meals/home.html')

def daily_submission_view(request):
    if request.method == "POST":
        form = DailySubmissionForm(request.POST)
        dish_form = DishForm(request.POST)
        if form.is_valid() and dish_form.is_valid():
            submission = form.save()
            dish = dish_form.save()
            for dish_ingredient in DishIngredient.objects.filter(dish=submission.dish):
                grams_used = request.POST.get(f'ingredient_{dish_ingredient.ingredient.id}')
                if grams_used:
                    try:
                        grams_used = float(grams_used)
                        cost_per_gram = dish_ingredient.ingredient.cost_per_gram
                        DailySubmissionIngredient.objects.create(
                            submission=submission,
                            dish_ingredient=dish_ingredient,
                            grams_used=grams_used,
                            cost_per_gram=cost_per_gram
                        )
                    except ValueError:
                        # Handle the error if grams_used is not a valid float
                        pass
            return redirect('submissions_list')
    else:
        form = DailySubmissionForm()
        dish_form = DishForm()
    return render(request, 'meals/daily_submission.html', {'form': form, 'dish_form': dish_form})

def submission_success(request):
    return render(request, 'meals/submission_success.html')

def get_ingredients(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    ingredients = [{'id': di.id, 'name': di.ingredient.name, 'cost_per_gram': di.ingredient.cost_per_gram} for di in dish.dish_ingredients.all()]
    return JsonResponse({'ingredients': ingredients})

def submissions_list_view(request):
    submissions = DailySubmission.objects.all().order_by('-submission_date')
    return render(request, 'meals/list_submissions.html', {'submissions': submissions})

def submission_detail_view(request, pk):
    submission = get_object_or_404(DailySubmission, pk=pk)
    submission_ingredients = DailySubmissionIngredient.objects.filter(submission=submission)
    
    total_calories = 0
    total_protein = 0
    total_fats = 0
    total_carbohydrates = 0
    total_cost = 0
    
    for submission_ingredient in submission_ingredients:
        ingredient = submission_ingredient.dish_ingredient.ingredient
        grams_used = submission_ingredient.grams_used
        current_cost_per_gram = ingredient.cost_per_gram  # Fetch the current cost_per_gram from the Ingredient model
        total_calories += ingredient.calories_per_gram * grams_used
        total_protein += ingredient.protein_per_gram * grams_used
        total_fats += ingredient.fats_per_gram * grams_used
        total_carbohydrates += ingredient.carbohydrates_per_gram * grams_used
        total_cost += current_cost_per_gram * grams_used
    
    context = {
        'submission': submission,
        'submission_ingredients': submission_ingredients,
        'total_calories': round(total_calories, 2),
        'total_protein': round(total_protein, 2),
        'total_fats': round(total_fats, 2),
        'total_carbohydrates': round(total_carbohydrates, 2),
        'total_cost': round(total_cost, 2),
    }
    return render(request, 'meals/submission_detail.html', context)

def submission_view(request, submission_id):
    submission = get_object_or_404(DailySubmission, id=submission_id)
    dish_ingredients = DishIngredient.objects.filter(dish=submission.dish)
    
    context = {
        'submission': submission,
        'dish_ingredients': dish_ingredients,
    }
    return render(request, 'meals/submission_detail.html', context)
