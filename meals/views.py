from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .forms import DailySubmissionForm, DishForm
from .models import DailySubmission, DishIngredient, DailySubmissionIngredient, Dish

def home_view(request):
    return render(request, 'meals/home.html')

def daily_submission_view(request):
    if request.method == "POST":
        form = DailySubmissionForm(request.POST)
        dish_form = DishForm(request.POST)
        if form.is_valid() and dish_form.is_valid():
            submission = form.save()
            dish = dish_form.save(commit=False)
            dish.save()
            for dish_ingredient in submission.dish.dish_ingredients.all():
                grams_used = request.POST.get(f'grams_used_{dish_ingredient.id}')
                if grams_used:
                    DailySubmissionIngredient.objects.create(
                        submission=submission,
                        dish_ingredient=dish_ingredient,
                        grams_used=float(grams_used)
                    )
            return redirect('submission_success')
    else:
        form = DailySubmissionForm()
        dish_form = DishForm()
    return render(request, 'meals/daily_submission.html', {'form': form, 'dish_form': dish_form})

def submission_success(request):
    return render(request, 'meals/submission_success.html')

def get_ingredients(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    ingredients = [{'id': di.id, 'name': di.ingredient.name} for di in dish.dish_ingredients.all()]
    return JsonResponse({'ingredients': ingredients})

def submissions_list_view(request):
    submissions = DailySubmission.objects.all().order_by('-submission_date')
    return render(request, 'meals/list_submissions.html', {'submissions': submissions})

def submission_detail_view(request, pk):
    submission = get_object_or_404(DailySubmission, pk=pk)
    return render(request, 'meals/submission_detail.html', {'submission': submission})
