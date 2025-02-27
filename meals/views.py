from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .forms import DailySubmissionForm, DishForm, CalorieGoalRangeForm, AcneEntryForm, SkinProductForm
from .models import DailySubmission, DishIngredient, DailySubmissionIngredient, Dish, Ingredient, DailyCalorieGoal, AcneEntry, SkinProduct
from .custom_calendar import CustomHTMLCalendar
from django.core.cache import cache
import calendar
from datetime import date, datetime, timedelta
from .models import Task, SubTask
from django.utils import timezone
import json

def home_view(request):
    return render(request, 'meals/home.html')

def calculate_dish(request):
    """Calculate adjusted ingredients based on nutritional targets"""
    if request.method == 'POST':
        data = json.loads(request.body)
        dish_id = data.get('dish_id')
        calorie_target = float(data.get('calorie_target', 0))
        protein_target = float(data.get('protein_target', 0))
        
        dish = get_object_or_404(Dish, id=dish_id)
        dish_ingredients = DishIngredient.objects.filter(dish=dish).select_related('ingredient')
        
        # Check if the dish has any ingredients
        if not dish_ingredients.exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Dish "{dish.name}" has no ingredients defined. Please add ingredients in the admin interface.'
            })
        
        # Calculate base nutritional values
        base_calories = 0
        base_protein = 0
        base_fats = 0
        base_carbs = 0
        
        # Debug information
        ingredient_details = []
        missing_quantities = False
        missing_nutritional_data = False
        
        for di in dish_ingredients:
            ingredient = di.ingredient
            # If default_quantity is None or 0, use a default value of 100g for calculation
            quantity = di.default_quantity if di.default_quantity else 100
            
            if not di.default_quantity:
                missing_quantities = True
            
            # Check if nutritional values exist
            if (ingredient.calories_per_gram == 0 and 
                ingredient.protein_per_gram == 0 and 
                ingredient.fats_per_gram == 0 and 
                ingredient.carbohydrates_per_gram == 0):
                missing_nutritional_data = True
            
            # Add to base values
            base_calories += ingredient.calories_per_gram * quantity
            base_protein += ingredient.protein_per_gram * quantity
            base_fats += ingredient.fats_per_gram * quantity
            base_carbs += ingredient.carbohydrates_per_gram * quantity
            
            ingredient_details.append({
                'name': ingredient.name,
                'quantity': quantity,
                'calories': ingredient.calories_per_gram * quantity,
                'protein': ingredient.protein_per_gram * quantity
            })
        
        # Add warning messages
        warning_message = ""
        if missing_quantities:
            warning_message += "Some ingredients have no default quantity. Using 100g as a fallback. "
        if missing_nutritional_data:
            warning_message += "Some ingredients have missing nutritional data. "
        
        # Determine adjustment factor (avoid division by zero)
        calorie_adjustment = calorie_target / max(base_calories, 0.001)
        protein_adjustment = protein_target / max(base_protein, 0.001)
        adjustment_factor = max(calorie_adjustment, protein_adjustment)
        
        # Calculate adjusted values
        adjusted_calories = base_calories * adjustment_factor
        adjusted_protein = base_protein * adjustment_factor
        adjusted_fats = base_fats * adjustment_factor
        adjusted_carbs = base_carbs * adjustment_factor
        
        # Generate ingredient list with adjusted quantities
        ingredients = []
        total_cost = 0
        
        for di in dish_ingredients:
            ingredient = di.ingredient
            base_quantity = di.default_quantity if di.default_quantity else 100
            adjusted_quantity = base_quantity * adjustment_factor
            
            ingredients.append({
                'name': ingredient.name,
                'base_quantity': base_quantity,
                'adjusted_quantity': adjusted_quantity,
                'cost_per_gram': ingredient.cost_per_gram
            })
            
            total_cost += adjusted_quantity * ingredient.cost_per_gram
        
        return JsonResponse({
            'status': 'success',
            'dish_name': dish.name,
            'base_calories': round(base_calories, 2),
            'base_protein': round(base_protein, 2),
            'base_fats': round(base_fats, 2),
            'base_carbs': round(base_carbs, 2),
            'adjusted_calories': round(adjusted_calories, 2),
            'adjusted_protein': round(adjusted_protein, 2),
            'adjusted_fats': round(adjusted_fats, 2),
            'adjusted_carbs': round(adjusted_carbs, 2),
            'adjustment_factor': adjustment_factor,
            'ingredients': ingredients,
            'total_cost': total_cost,
            'warning': warning_message if warning_message else None,
            'debug_info': ingredient_details
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def dish_calculator_view(request):
    """View for calculating a single dish with specific nutritional targets"""
    dishes = Dish.objects.all().order_by('name')
    return render(request, 'meals/dish_calculator.html', {'dishes': dishes})

def generate_grocery_list(request):
    """Generate a grocery list based on the meal plan"""
    if request.method == 'POST':
        data = json.loads(request.body)
        meal_plan = data.get('meal_plan', {})
        
        # Aggregate ingredients across all meals
        grocery_list = {}
        total_cost = 0
        
        for date_str, meals in meal_plan.items():
            for meal_type, meal_details in meals.items():
                dish_id = meal_details.get('dish_id')
                servings = float(meal_details.get('servings', 1))
                calorie_target = float(meal_details.get('calorie_target', 0))
                
                if dish_id:
                    dish = get_object_or_404(Dish, id=dish_id)
                    
                    # Calculate base nutrition values
                    base_calories = 0
                    dish_ingredients = DishIngredient.objects.filter(dish=dish)
                    
                    for di in dish_ingredients:
                        ingredient = di.ingredient
                        quantity = di.default_quantity or 0
                        base_calories += ingredient.calories_per_gram * quantity
                    
                    # Calculate adjustment factor based on calorie target
                    adjustment_factor = calorie_target / base_calories if base_calories > 0 else 1
                    
                    # Adjust ingredient quantities
                    for di in dish_ingredients:
                        ingredient = di.ingredient
                        base_quantity = di.default_quantity or 0
                        adjusted_quantity = base_quantity * adjustment_factor * servings
                        
                        if ingredient.id in grocery_list:
                            grocery_list[ingredient.id]['quantity'] += adjusted_quantity
                        else:
                            grocery_list[ingredient.id] = {
                                'name': ingredient.name,
                                'quantity': adjusted_quantity,
                                'cost_per_gram': ingredient.cost_per_gram
                            }
                        
                        # Update total cost
                        total_cost += adjusted_quantity * ingredient.cost_per_gram
        
        # Convert dictionary to list for the response
        grocery_items = list(grocery_list.values())
        
        return JsonResponse({
            'groceries': grocery_items,
            'total_cost': round(total_cost, 2)
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
def meal_planner_view(request):
    """View for the weekly meal planner interface"""
    # Get all available dishes
    dishes = Dish.objects.all().order_by('name')
    
    # Get the current week's dates
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    week_dates = [(start_of_week + timedelta(days=i)) for i in range(7)]
    
    context = {
        'dishes': dishes,
        'week_dates': week_dates,
    }
    
    return render(request, 'meals/meal_planner.html', context)


def acne_home(request):
    entries = AcneEntry.objects.all().order_by('-entry_date')[:5]  # Latest 5 entries
    products = SkinProduct.objects.all()
    
    context = {
        'recent_entries': entries,
        'products': products,
    }
    return render(request, 'meals/acne_home.html', context)

def acne_entry_create(request):
    if request.method == 'POST':
        form = AcneEntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.save()
            
            # Handle selected products
            form.save_m2m()  # Save the many-to-many relationships
            
            # Handle new product creation if provided
            new_product = request.POST.get('new_product')
            if new_product:
                brand = request.POST.get('new_product_brand', '')
                product = SkinProduct.objects.create(
                    name=new_product,
                    brand=brand
                )
                entry.products_used.add(product)
                
            return redirect('acne_history')
    else:
        form = AcneEntryForm()
    
    return render(request, 'meals/acne_entry_form.html', {'form': form})

def acne_history(request):
    entries = AcneEntry.objects.all().order_by('-entry_date')
    
    # Group entries by month for easier browsing
    grouped_entries = {}
    for entry in entries:
        month_year = f"{entry.entry_date.strftime('%B %Y')}"
        if month_year not in grouped_entries:
            grouped_entries[month_year] = []
        grouped_entries[month_year].append(entry)
    
    return render(request, 'meals/acne_history.html', {
        'grouped_entries': grouped_entries,
    })

def acne_entry_detail(request, entry_id):
    entry = get_object_or_404(AcneEntry, id=entry_id)
    
    # Find previous and next entries for navigation
    prev_entry = AcneEntry.objects.filter(entry_date__lt=entry.entry_date).order_by('-entry_date').first()
    next_entry = AcneEntry.objects.filter(entry_date__gt=entry.entry_date).order_by('entry_date').first()
    
    context = {
        'entry': entry,
        'prev_entry': prev_entry,
        'next_entry': next_entry,
    }
    return render(request, 'meals/acne_entry_detail.html', context)

def product_analysis(request):
    products = SkinProduct.objects.all()
    product_analysis = {}
    
    for product in products:
        entries = AcneEntry.objects.filter(products_used=product).order_by('entry_date')
        if entries:
            # Calculate average severity when using this product
            avg_severity = sum(entry.severity for entry in entries) / len(entries)
            # Get the trend by comparing first and last entry
            if len(entries) >= 2:
                first_severity = entries.first().severity
                last_severity = entries.last().severity
                trend = last_severity - first_severity  # Negative is improvement
            else:
                trend = 0
                
            product_analysis[product] = {
                'avg_severity': round(avg_severity, 1),
                'num_uses': len(entries),
                'trend': trend,
                'last_used': entries.last().entry_date
            }
    
    return render(request, 'meals/product_analysis.html', {
        'product_analysis': product_analysis
    })























def dashboard_view(request):
    now = datetime.now()
    year, month = now.year, now.month

    # --- Process the Calorie Goal Range Form ---
    if request.method == 'POST' and 'set_goal' in request.POST:
        form = CalorieGoalRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            calorie_goal = form.cleaned_data['calorie_goal']

            # Update or create a DailyCalorieGoal for each date in the range
            current = start_date
            while current <= end_date:
                # Latest assignment overrides any previous goal.
                DailyCalorieGoal.objects.update_or_create(
                    date=current,
                    defaults={'calorie_goal': calorie_goal}
                )
                current += timedelta(days=1)
            return redirect('dashboard')
    else:
        form = CalorieGoalRangeForm()

    # --- Aggregate Calorie Data ---
    # Use caching for performance (cache key includes year and month)
    cache_key = f"daily_totals_{year}_{month}"
    daily_totals = cache.get(cache_key)
    if daily_totals is None:
        daily_totals = {}
        # Iterate over submissions in the current month
        submissions = DailySubmission.objects.filter(
            submission_date__year=year, submission_date__month=month
        )
        # Loop through submissions and add calories together.
        # (Assuming each submission has a method or property to calculate total calories)
        for submission in submissions:
            sub_date = submission.submission_date
            # Calculate calories for this submission
            total_calories = 0
            for ingredient in submission.ingredients.all():
                # Assuming each ingredient has calories_per_gram and grams_used on the submission ingredient
                total_calories += ingredient.dish_ingredient.ingredient.calories_per_gram * ingredient.grams_used
            daily_totals[sub_date] = daily_totals.get(sub_date, 0) + round(total_calories)

        # Cache the result for one hour (3600 seconds)
        cache.set(cache_key, daily_totals, timeout=3600)

    # --- Retrieve Calorie Goals for the Month ---
    goals = DailyCalorieGoal.objects.filter(date__year=year, date__month=month)
    goal_map = {goal.date: goal.calorie_goal for goal in goals}

    # --- Build Day Data Dictionary ---
    # We’ll create a dictionary mapping each day (as a date object) in the month to a tuple (total_calories, calorie_goal)
    day_data = {}
    # Get the number of days in the month
    num_days = calendar.monthrange(year, month)[1]
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        eaten = daily_totals.get(current_date, 0)
        goal = goal_map.get(current_date, 0)  # default goal is 0 unless explicitly set
        day_data[current_date] = (eaten, goal)

    # --- Generate the Calendar HTML ---
    cal = CustomHTMLCalendar(year, month, day_data).formatmonth(withyear=True)

    context = {
        'calendar': cal,
        'goal_form': form,
    }
    return render(request, 'meals/dashboard.html', context)

def wir_view(request):
    # Logic for the WIR page
    return render(request, 'meals/wir.html')  # Create a new template for WIR

def daily_submission_view(request):
    submission_ingredients = []  # Initialize the variable outside if/else blocks
    
    if request.method == "POST":
        form = DailySubmissionForm(request.POST, request.FILES)  # Include request.FILES for file uploads
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

    return render(request, 'meals/daily_submission.html', {
        'form': form,
        'dish_form': dish_form,
        'submission_ingredients': submission_ingredients
    })

def submission_success(request):
    return render(request, 'meals/submission_success.html')

def get_ingredients(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    ingredients = [{'id': di.id, 'name': di.ingredient.name, 'cost_per_gram': di.ingredient.cost_per_gram} for di in dish.dish_ingredients.all()]
    return JsonResponse({'ingredients': ingredients})

def submissions_list_view(request):
    submissions = DailySubmission.objects.all().order_by('-submission_date')

    # Initialize a list to store submission-specific totals
    submission_totals = []

    for submission in submissions:
        total_calories = 0
        total_protein = 0
        total_fats = 0
        total_carbohydrates = 0
        total_cost = 0

        for submission_ingredient in submission.ingredients.all():
            ingredient = submission_ingredient.dish_ingredient.ingredient
            grams_used = submission_ingredient.grams_used
            current_cost_per_gram = ingredient.cost_per_gram  # Fetch the current cost_per_gram from the Ingredient model
            total_calories += ingredient.calories_per_gram * grams_used
            total_protein += ingredient.protein_per_gram * grams_used
            total_fats += ingredient.fats_per_gram * grams_used
            total_carbohydrates += ingredient.carbohydrates_per_gram * grams_used
            total_cost += current_cost_per_gram * grams_used
        
        # Append the calculated totals for this submission to the list
        submission_totals.append({
            'submission': submission,
            'total_calories': round(total_calories, 2),
            'total_protein': round(total_protein, 2),
            'total_fats': round(total_fats, 2),
            'total_carbohydrates': round(total_carbohydrates, 2),
            'total_cost': round(total_cost, 2)
        })
    
    context = {
        'submissions': submission_totals  # Pass the list of submission-specific totals
    }
    
    return render(request, 'meals/list_submissions.html', context)

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
    
    # Format the total_cost with a dollar sign
    formatted_total_cost = f"${round(total_cost, 2)}"
    
    context = {
        'submission': submission,
        'submission_ingredients': submission_ingredients,
        'total_calories': round(total_calories, 2),
        'total_protein': round(total_protein, 2),
        'total_fats': round(total_fats, 2),
        'total_carbohydrates': round(total_carbohydrates, 2),
        'total_cost': formatted_total_cost,  # Pass the formatted cost
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

def delete_submission(request, submission_id):
    # Retrieve the submission object or return a 404 if it doesn't exist
    submission = get_object_or_404(DailySubmission, id=submission_id)
    
    if request.method == 'POST':
        # Delete the submission and all related DailySubmissionIngredient objects (via cascade)
        submission.delete()
        return redirect('submissions_list')
    
    # Optionally, render a confirmation page if you want a separate confirmation step:
    return render(request, 'meals/confirm_delete.html', {'submission': submission})

def wir_view(request):
    if request.method == "POST":
        # Retrieve task information from the form submission
        task_title = request.POST.get("task_title")
        # The timer is running on the client, and when stopped the duration (in seconds) is submitted
        duration_seconds = float(request.POST.get("task_duration", 0))
        duration = timedelta(seconds=duration_seconds)

        # For simplicity, we store start_time and end_time as the time of submission.
        now = timezone.now()
        task = Task.objects.create(
            title=task_title,
            start_time=now,
            end_time=now,
            duration=duration,
            date=now.date()
        )
        
        # Process subtasks data
        subtasks_data = request.POST.get("subtasks_data")
        if subtasks_data:
            try:
                subtasks = json.loads(subtasks_data)
                
                # Create a map to track parent-child relationships
                subtask_map = {}
                
                # First pass: Create all subtasks
                for subtask_info in subtasks:
                    subtask_duration = timedelta(seconds=float(subtask_info.get("duration", 0)))
                    
                    subtask = SubTask.objects.create(
                        task=task,
                        title=subtask_info["title"],
                        start_time=now,
                        end_time=now,
                        duration=subtask_duration,
                        # Parent will be set in the second pass
                    )
                    
                    # Store the ID mapping
                    subtask_map[subtask_info["id"]] = subtask
                
                # Second pass: Set parent-child relationships
                for subtask_info in subtasks:
                    if subtask_info.get("parentId"):
                        # Find the Django model instances
                        child = subtask_map.get(subtask_info["id"])
                        parent = subtask_map.get(subtask_info["parentId"])
                        
                        if child and parent:
                            child.parent = parent
                            child.save()
                            
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Log the error but continue
                print(f"Error processing subtasks: {e}")
        
        return redirect("wir_view")
    
    tasks = Task.objects.all().order_by("-id")
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    # Sum durations (in seconds) for today and this week
    daily_total = sum((t.duration.total_seconds() for t in tasks if t.date == today), 0)
    weekly_total = sum((t.duration.total_seconds() for t in tasks if t.date >= start_of_week), 0)
    total_tasks = tasks.count()

    context = {
        "tasks": tasks,
        "daily_total": daily_total,
        "weekly_total": weekly_total,
        "total_tasks": total_tasks,
    }
    return render(request, "meals/wir.html", context)