from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods  # Add this import
from .forms import DailySubmissionForm, DishForm, CalorieGoalRangeForm, AcneEntryForm, SkinProductForm, ProfileSelectForm
from .models import DailySubmission, DishIngredient, DailySubmissionIngredient, Dish, Ingredient, DailyCalorieGoal, AcneEntry, SkinProduct, Task, SubTask, Profile, WeightMeasurement, Habit, HabitCompletion, Notification, PushSubscription
from .custom_calendar import CustomHTMLCalendar
from django.core.cache import cache
import calendar
from datetime import date, datetime, timedelta
from django.utils import timezone
import json
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
from django.conf import settings

@require_POST
def push_subscribe(request):
    try:
        data = json.loads(request.body)
        subscription = data.get('subscription')
        
        if not subscription:
            return JsonResponse({'status': 'error', 'message': 'No subscription data provided'}, status=400)
            
        # Store the subscription in your database
        PushSubscription.objects.create(
            user=request.user,
            endpoint=subscription.get('endpoint'),
            p256dh=subscription.get('keys', {}).get('p256dh'),
            auth=subscription.get('keys', {}).get('auth')
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# Remove the first set of notification functions and keep only these ones with both decorators
# Notification API endpoints
@csrf_exempt
@require_http_methods(["GET"])
def get_notification(request, notification_id):
    """API endpoint to get a notification's details"""
    notification = get_object_or_404(Notification, id=notification_id)
    return JsonResponse({
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'frequency': notification.frequency,
        'enabled': notification.enabled
    })

@csrf_exempt
@require_http_methods(["POST"])
def create_notification(request):
    """API endpoint to create a new notification"""
    data = json.loads(request.body)
    
    notification = Notification(
        title=data.get('title'),
        message=data.get('message'),
        frequency=data.get('frequency', 'weekly'),
        enabled=data.get('enabled', True)
    )
    notification.calculate_next_send()
    notification.save()
    
    return JsonResponse({'status': 'success', 'id': notification.id})

@csrf_exempt
@require_http_methods(["POST"])
def update_notification(request, notification_id):
    """API endpoint to update an existing notification"""
    notification = get_object_or_404(Notification, id=notification_id)
    data = json.loads(request.body)
    
    notification.title = data.get('title', notification.title)
    notification.message = data.get('message', notification.message)
    notification.frequency = data.get('frequency', notification.frequency)
    notification.enabled = data.get('enabled', notification.enabled)
    
    notification.calculate_next_send()
    notification.save()
    
    return JsonResponse({'status': 'success'})

@csrf_exempt
@require_http_methods(["POST"])
def delete_notification(request, notification_id):
    """API endpoint to delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    
    return JsonResponse({'status': 'success'})

@csrf_exempt
@require_http_methods(["POST"])
def test_notification(request, notification_id):
    """API endpoint to test a notification"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    # In a real implementation, you would send the actual push notification here
    
    return JsonResponse({
        'status': 'success',
        'title': notification.title,
        'message': notification.message
    })

# In your view that renders the notifications template
def notifications_view(request):
    # Get your notifications
    notifications = Notification.objects.all()
    
    # Import at the top of the function
    from django.conf import settings
    
    # Use a default empty string if setting doesn't exist
    vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
    
    # Debug prints
    print(f"VAPID key being sent to template: {vapid_public_key}")
    print(f"VAPID key length: {len(vapid_public_key)}")
    
    return render(request, 'meals/notifications.html', {
        'notifications': notifications,
        'vapid_public_key': vapid_public_key
    })

@csrf_exempt
def weight_api(request):
    if request.method == 'POST':
        try:
            print(f"Request body: {request.body}")  # Debug logging
            
            data = json.loads(request.body)
            print(f"Parsed data: {data}")  # Debug logging
            
            # Get weight value
            weight_val = data.get('weight')
            # Handle if weight comes as string with unit
            if isinstance(weight_val, str) and ' ' in weight_val:
                parts = weight_val.split()
                weight = float(parts[0])
            else:
                weight = float(weight_val)
                
            date = data.get('date')
            profile_id = data.get('profile_id', 1)
            
            # Create profile if doesn't exist
            profile, created = Profile.objects.get_or_create(
                id=profile_id, 
                defaults={'name': f'Profile {profile_id}'}
            )
            
            # Create weight entry
            measurement, created = WeightMeasurement.objects.update_or_create(
                profile=profile,
                date=date,
                defaults={'weight': weight}
            )
            
            return JsonResponse({
                'status': 'success',
                'weight': weight,
                'date': date
            })
        except Exception as e:
            import traceback
            print(f"Error in weight_api: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def import_weight_data(request):
    if request.method == 'POST' and request.FILES.get('health_export'):
        health_file = request.FILES['health_export']
        profile_id = request.POST.get('profile')
        profile = get_object_or_404(Profile, id=profile_id)
        
        # Parse XML file
        import xml.etree.ElementTree as ET
        try:
            tree = ET.parse(health_file)
            root = tree.getroot()
            
            # Find weight records in the export
            records = root.findall(".//Record[@type='HKQuantityTypeIdentifierBodyMass']")
            
            count = 0
            for record in records:
                date_str = record.get('startDate').split()[0]
                weight_val = float(record.get('value'))
                
                # Convert pounds to kg if needed
                if record.get('unit') == 'lb':
                    weight_val *= 0.45359237
                    
                # Create or update weight record
                WeightMeasurement.objects.update_or_create(
                    profile=profile,
                    date=date_str,
                    defaults={'weight': weight_val}
                )
                count += 1
                
            messages.success(request, f"Successfully imported {count} weight measurements")
        except Exception as e:
            messages.error(request, f"Error parsing health data: {str(e)}")
            
    return render(request, 'meals/import_weight.html', {
        'profiles': Profile.objects.all()
    })



# Try to import Workout models if they exist
try:
    from .models import Workout, Exercise, WorkoutExercise, ExerciseSet, WorkoutPreset, PresetExercise
    WORKOUT_MODELS_EXIST = True
except ImportError:
    WORKOUT_MODELS_EXIST = False

def home_view(request):
    """Home page view"""
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
        
        # Find the ingredient with highest protein content
        highest_protein_ingredient = None
        highest_protein_content = 0
        highest_protein_per_gram = 0
        
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
            
            # Calculate protein content for this ingredient
            protein_content = ingredient.protein_per_gram * quantity
            
            # Track highest protein ingredient
            if ingredient.protein_per_gram > highest_protein_per_gram:
                highest_protein_per_gram = ingredient.protein_per_gram
                highest_protein_ingredient = di
                highest_protein_content = protein_content
            
            # Add to base values
            base_calories += ingredient.calories_per_gram * quantity
            base_protein += protein_content
            base_fats += ingredient.fats_per_gram * quantity
            base_carbs += ingredient.carbohydrates_per_gram * quantity
            
            ingredient_details.append({
                'name': ingredient.name,
                'quantity': quantity,
                'calories': ingredient.calories_per_gram * quantity,
                'protein': protein_content
            })
        
        # Add warning messages
        warning_message = ""
        if missing_quantities:
            warning_message += "Some ingredients have no default quantity. Using 100g as a fallback. "
        if missing_nutritional_data:
            warning_message += "Some ingredients have missing nutritional data. "
        
        # Determine if we're prioritizing calories or protein
        if protein_target > 0 and protein_target > base_protein:
            # Calculate how much additional protein we need
            protein_needed = protein_target - base_protein
            
            # Calculate how much of high-protein ingredient to add to reach target
            if highest_protein_per_gram > 0:
                additional_protein_ingredient = protein_needed / highest_protein_per_gram
                high_protein_scaling = (highest_protein_ingredient.default_quantity + additional_protein_ingredient) / highest_protein_ingredient.default_quantity
            else:
                high_protein_scaling = protein_target / max(base_protein, 0.001)
            
            # Scale other ingredients more conservatively
            other_scaling = min(1.5, max(1.0, high_protein_scaling * 0.4))
            
            # Generate ingredient list with intelligent scaling
            ingredients = []
            total_cost = 0
            adjusted_calories = 0
            adjusted_protein = 0
            adjusted_fats = 0
            adjusted_carbs = 0
            
            for di in dish_ingredients:
                ingredient = di.ingredient
                base_quantity = di.default_quantity if di.default_quantity else 100
                
                # Apply different scaling factors
                if di == highest_protein_ingredient:
                    scaling = high_protein_scaling
                else:
                    scaling = other_scaling
                
                adjusted_quantity = base_quantity * scaling
                
                # Update adjusted nutrition totals
                adjusted_calories += ingredient.calories_per_gram * adjusted_quantity
                adjusted_protein += ingredient.protein_per_gram * adjusted_quantity
                adjusted_fats += ingredient.fats_per_gram * adjusted_quantity
                adjusted_carbs += ingredient.carbohydrates_per_gram * adjusted_quantity
                
                ingredients.append({
                    'name': ingredient.name,
                    'base_quantity': base_quantity,
                    'adjusted_quantity': adjusted_quantity,
                    'cost_per_gram': ingredient.cost_per_gram
                })
                
                total_cost += adjusted_quantity * ingredient.cost_per_gram
                
            # For display, use protein-based adjustment factor
            adjustment_factor = high_protein_scaling
        else:
            # Use standard calorie-based adjustment
            calorie_adjustment = calorie_target / max(base_calories, 0.001)
            adjustment_factor = calorie_adjustment
            
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
    """API view for generating a grocery list based on the meal plan"""
    if request.method == 'POST':
        data = json.loads(request.body)
        meal_plan = data.get('meal_plan', {})
        
        grocery_list = {}
        total_cost = 0
        
        for date_str, meals in meal_plan.items():
            for meal_type, meal_details in meals.items():
                dish_id = meal_details.get('dish_id')
                servings = float(meal_details.get('servings', 1))
                calorie_target = float(meal_details.get('calorie_target', 0))
                
                if dish_id:
                    dish = get_object_or_404(Dish, id=dish_id)
                    dish_ingredients = DishIngredient.objects.filter(dish=dish)
                    
                    # Get original recipe proportions
                    original_quantities = {}
                    original_calories = 0
                    
                    for di in dish_ingredients:
                        quantity = di.default_quantity or 0
                        original_quantities[di.id] = quantity
                        original_calories += di.ingredient.calories_per_gram * quantity
                    
                    # Calculate overall scaling factor for calories
                    cal_scaling = calorie_target / max(original_calories, 0.001)
                    
                    # Apply recipe-proportional scaling
                    for di in dish_ingredients:
                        ingredient = di.ingredient
                        original_qty = original_quantities[di.id]
                        adjusted_qty = original_qty * cal_scaling * servings
                        
                        if ingredient.id in grocery_list:
                            grocery_list[ingredient.id]['quantity'] += adjusted_qty
                        else:
                            grocery_list[ingredient.id] = {
                                'name': ingredient.name,
                                'quantity': adjusted_qty,
                                'cost_per_gram': ingredient.cost_per_gram
                            }
                        
                        total_cost += adjusted_qty * ingredient.cost_per_gram
        
        grocery_items = list(grocery_list.values())
        return JsonResponse({'groceries': grocery_items, 'total_cost': round(total_cost, 2)})
    
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
    """View for the acne tracker home page"""
    entries = AcneEntry.objects.all().order_by('-entry_date')[:5]  # Latest 5 entries
    products = SkinProduct.objects.all()
    
    context = {
        'recent_entries': entries,
        'products': products,
    }
    return render(request, 'meals/acne_home.html', context)

def acne_entry_create(request):
    """View for creating a new acne entry"""
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
    """View for the acne tracker history page"""
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
    """View for viewing the details of an acne entry"""
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
    """View for analyzing the effectiveness of skin products"""
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
    """Dashboard view for monitoring nutrition data"""
    now = datetime.now()
    year, month = now.year, now.month
    
    # Initialize context at the beginning
    context = {}
    
    if not Profile.objects.exists():
        Profile.objects.create(name="Default Profile")

    selected_profile = Profile.objects.first()

    recent_weights = WeightMeasurement.objects.filter(
        profile=selected_profile
    ).order_by('-date')[:10] 

    if request.method == "POST" and 'select_profile' in request.POST:
        profile_form = ProfileSelectForm(request.POST)
        if profile_form.is_valid():
            selected_profile = profile_form.cleaned_data['profile']
    else:
        # Check for profile in GET parameters
        profile_id = request.GET.get('profile')
        if profile_id:
            try:
                selected_profile = Profile.objects.get(id=profile_id)
            except (Profile.DoesNotExist, ValueError):
                pass
        
        profile_form = ProfileSelectForm(initial={'profile': selected_profile})

    # --- Process the Calorie Goal Range Form ---
    if request.method == 'POST' and 'set_goal' in request.POST:
        form = CalorieGoalRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            calorie_goal = form.cleaned_data['calorie_goal']
            profile = form.cleaned_data['profile']

            # Update or create a DailyCalorieGoal for each date in the range
            current = start_date
            while current <= end_date:
                # Latest assignment overrides any previous goal.
                DailyCalorieGoal.objects.update_or_create(
                    date=current,
                    profile=profile,
                    defaults={'calorie_goal': calorie_goal}
                )
                current += timedelta(days=1)
            return redirect('dashboard')
    else:
        form = CalorieGoalRangeForm(initial={'profile': selected_profile})

    # --- Aggregate Calorie Data ---
    # Use caching for performance (cache key includes year and month)
    cache_key = f"daily_totals_{year}_{month}_{selected_profile.id}"
    daily_totals = cache.get(cache_key)
    if daily_totals is None:
        daily_totals = {}
        # Iterate over submissions in the current month
        submissions = DailySubmission.objects.filter(
            submission_date__year=year, submission_date__month=month,
            profile=selected_profile
        )
        # Loop through submissions and add calories together.
        for submission in submissions:
            sub_date = submission.submission_date
            # Calculate calories for this submission
            total_calories = 0
            for ingredient in submission.ingredients.all():
                # Assuming each ingredient has calories_per_gram and grams_used on the submission ingredient
                total_calories += ingredient.dish_ingredient.ingredient.calories_per_gram * ingredient.grams_used
            daily_totals[sub_date] = daily_totals.get(sub_date, 0) + round(total_calories)

        # Cache the result for one hour
        cache.set(cache_key, daily_totals, timeout=3600)

    # --- Retrieve Calorie Goals for the Month ---
    goals = DailyCalorieGoal.objects.filter(date__year=year, date__month=month, profile=selected_profile)
    goal_map = {goal.date: goal.calorie_goal for goal in goals}

    # --- Build Day Data Dictionary ---
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

    # Process weight data
    weight_data = []
    weights = WeightMeasurement.objects.filter(profile=selected_profile).order_by('date')
    for weight in weights:
        weight_data.append({
            'date': weight.date.strftime('%Y-%m-%d'),
            'weight': weight.weight
        })
    
    # Add weight data to context
    context['weight_data'] = json.dumps(weight_data)

    # Update the main context dictionary
    context.update({
        'calendar': cal,
        'goal_form': form,
        'profile_form': profile_form,
        'profiles': Profile.objects.all(),
        'selected_profile': selected_profile,
        'recent_weights': recent_weights,
    })
    
    return render(request, 'meals/dashboard.html', context)

def weight_list(request):
    weights = WeightMeasurement.objects.all().order_by('-date')
    return render(request, 'meals/weight_list.html', {'weights': weights})


def wir_view(request):
    """View for the Work In Progress (WIR) tracking page"""
    if request.method == "POST":
        try:
            # Retrieve task information from the form submission
            task_title = request.POST.get("task_title", "Untitled Task")  # Default if missing
            
            try:
                duration_seconds = float(request.POST.get("task_duration", 0))
            except (ValueError, TypeError):
                duration_seconds = 0
                
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
                    
                    # Create a map to track created subtasks for parent-child relationships
                    subtask_map = {}
                    
                    # First pass: Create all subtasks
                    for subtask_info in subtasks:
                        try:
                            # Get duration with fallback to 0 if there's an error
                            try:
                                subtask_duration = timedelta(seconds=float(subtask_info.get("duration", 0)))
                            except (ValueError, TypeError):
                                subtask_duration = timedelta(seconds=0)
                                
                            # Get title with fallback
                            subtask_title = subtask_info.get("title", "Unnamed Subtask")
                            
                            # Get ID with fallback
                            subtask_id = subtask_info.get("id", f"temp-{uuid.uuid4()}")
                            
                            subtask = SubTask.objects.create(
                                task=task,
                                title=subtask_title,
                                start_time=now,
                                end_time=now,
                                duration=subtask_duration,
                            )
                            
                            # Store in map using the JavaScript ID
                            subtask_map[subtask_id] = subtask
                            
                        except Exception as e:
                            # Log error but continue with other subtasks
                            print(f"Error creating subtask: {e}")
                    
                    # Second pass: Set parent-child relationships
                    for subtask_info in subtasks:
                        try:
                            # If this subtask has a parent
                            parent_id = subtask_info.get("parentId")
                            subtask_id = subtask_info.get("id")
                            
                            if parent_id is not None and subtask_id in subtask_map:
                                child = subtask_map.get(subtask_id)
                                parent = subtask_map.get(parent_id)
                                
                                if child and parent:
                                    child.parent = parent
                                    child.save()
                        except Exception as e:
                            # Log error but continue with other relationships
                            print(f"Error setting parent-child relationship: {e}")
                                
                except json.JSONDecodeError as e:
                    print(f"Error parsing subtasks JSON: {e}")
                except Exception as e:
                    print(f"Error processing subtasks data: {e}")
            
            return redirect("wir_view")
            
        except Exception as e:
            # Catch all errors in POST handling
            print(f"Error processing WIR form: {e}")
            messages.error(request, "There was an error processing your task. Please try again.")
            # Return to the form page instead of crashing
            
    # Normal GET request handling
    try:
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
    except Exception as e:
        print(f"Error rendering WIR page: {e}")
        return HttpResponse("An error occurred loading the WIR page. Please try again.")

def daily_submission_view(request):
    """View for submitting daily meals"""
    submission_ingredients = []  # Initialize the variable outside if/else blocks
    
    if request.method == "POST":
        form = DailySubmissionForm(request.POST, request.FILES)  # Include request.FILES for file uploads
        if form.is_valid():
            submission = form.save(commit=False)
            
            # Process feeling rating
            feeling_rating = request.POST.get('feeling_rating', 3)  # Default to 3 if not provided
            submission.feeling_rating = feeling_rating
            
            submission.save()
            
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

    # Get all profiles for the form
    profiles = Profile.objects.all()

    return render(request, 'meals/daily_submission.html', {
        'form': form,
        'submission_ingredients': submission_ingredients,
        'profiles': profiles
    })

def submission_success(request):
    """Success page after submitting a meal"""
    return render(request, 'meals/submission_success.html')

def get_ingredients(request, dish_id):
    """API view for getting ingredients for a dish"""
    dish = get_object_or_404(Dish, id=dish_id)
    ingredients = [{'id': di.id, 'name': di.ingredient.name, 'cost_per_gram': di.ingredient.cost_per_gram} for di in dish.dish_ingredients.all()]
    return JsonResponse({'ingredients': ingredients})

def submissions_list_view(request):
    """View for listing all meal submissions"""
    # Get filter by profile
    profile_id = request.GET.get('profile')
    selected_profile = None
    
    # Fetch all profiles for the filter dropdown
    profiles = Profile.objects.all()
    
    # Create base queryset
    submission_queryset = DailySubmission.objects.all()
    
    # Apply profile filter if specified
    if profile_id:
        try:
            selected_profile = Profile.objects.get(id=profile_id)
            submission_queryset = submission_queryset.filter(profile=selected_profile)
        except (Profile.DoesNotExist, ValueError):
            pass
            
    submissions = submission_queryset.order_by('-submission_date')

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
            current_cost_per_gram = ingredient.cost_per_gram or 0
            total_calories += ingredient.calories_per_gram * grams_used
            total_protein += ingredient.protein_per_gram * grams_used
            total_fats += ingredient.fats_per_gram * grams_used
            total_carbohydrates += ingredient.carbohydrates_per_gram * grams_used
            ingredient_cost = current_cost_per_gram * grams_used
            total_cost += ingredient_cost
        
        # Append the calculated totals for this submission to the list
        submission_totals.append({
            'submission': submission,
            'total_calories': round(total_calories, 2),
            'total_protein': round(total_protein, 2),
            'total_fats': round(total_fats, 2),
            'total_carbohydrates': round(total_carbohydrates, 2),
            'total_cost_per_serving': round(total_cost, 2)
        })
    
    context = {
        'submissions': submission_totals,
        'profiles': profiles,  # Make sure profiles are in the context
        'selected_profile': selected_profile
    }
    
    return render(request, 'meals/list_submissions.html', context)

def submission_detail_view(request, pk):
    """View for viewing the details of a meal submission"""
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
        current_cost_per_gram = ingredient.cost_per_gram
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
        'total_cost': formatted_total_cost,
    }
    
    return render(request, 'meals/submission_detail.html', context)

def submission_view(request, submission_id):
    """Alternative view for viewing a submission"""
    submission = get_object_or_404(DailySubmission, id=submission_id)
    dish_ingredients = DishIngredient.objects.filter(dish=submission.dish)
    
    context = {
        'submission': submission,
        'dish_ingredients': dish_ingredients,
    }
    return render(request, 'meals/submission_detail.html', context)

def delete_submission(request, submission_id):
    """View for deleting a meal submission"""
    submission = get_object_or_404(DailySubmission, id=submission_id)
    
    if request.method == 'POST':
        submission.delete()
        return redirect('submissions_list')
    
    return render(request, 'meals/confirm_delete.html', {'submission': submission})

# Workout views - only include if models exist
if WORKOUT_MODELS_EXIST:
    def workout_home(request):
        """View for the workout home page"""
        workouts = Workout.objects.all().order_by('-start_time')
        exercises = Exercise.objects.all().order_by('name')
        presets = WorkoutPreset.objects.all().order_by('name')
        
        context = {
            'workouts': workouts,
            'exercises': exercises,
            'presets': presets,
        }
        
        return render(request, 'meals/workout_home.html', context)

    def start_workout(request):
        """View for starting a new workout"""
        presets = WorkoutPreset.objects.all().order_by('name')
        
        if request.method == 'POST':
            preset_id = request.POST.get('preset_id')
            
            if preset_id:
                preset = get_object_or_404(WorkoutPreset, id=preset_id)
                workout = Workout.objects.create(preset=preset)
                
                # Add preset exercises to workout
                preset_exercises = PresetExercise.objects.filter(preset=preset).order_by('order')
                for i, preset_exercise in enumerate(preset_exercises):
                    # Include default sets and rep ranges in the notes field as JSON
                    notes = json.dumps({
                        'default_sets': preset_exercise.default_sets,
                        'min_reps': preset_exercise.min_reps,
                        'max_reps': preset_exercise.max_reps,
                        'custom_name': preset_exercise.custom_name
                    })
                    
                    WorkoutExercise.objects.create(
                        workout=workout,
                        exercise=preset_exercise.exercise,
                        order=i+1,
                        notes=notes
                    )
            else:
                workout = Workout.objects.create()
                
            return redirect('active_workout', workout_id=workout.id)
        
        # GET request - show the start workout page with preset selection
        return render(request, 'meals/start_workout.html', {'presets': presets})

    def active_workout(request, workout_id):
        """View for an active workout"""
        workout = get_object_or_404(Workout, id=workout_id)
        
        if not workout.is_active():
            return redirect('workout_detail', workout_id=workout.id)
        
        exercises = Exercise.objects.all().order_by('name')
        workout_exercises = WorkoutExercise.objects.filter(workout=workout)
        
        context = {
            'workout': workout,
            'exercises': exercises,
            'workout_exercises': workout_exercises,
        }
        
        return render(request, 'meals/active_workout.html', context)

    def finish_workout(request, workout_id):
        """View for finishing a workout"""
        workout = get_object_or_404(Workout, id=workout_id)
        
        if request.method == 'POST':
            workout.end_time = timezone.now()
            workout.duration = workout.calculate_duration()
            
            # Round the duration to seconds (remove microseconds)
            if workout.duration:
                seconds = workout.duration.total_seconds()
                workout.duration = timedelta(seconds=int(seconds))
                
            workout.save()
            
            return redirect('workout_detail', workout_id=workout.id)
        
        return redirect('active_workout', workout_id=workout.id)

    def workout_detail(request, workout_id):
        """View for viewing a completed workout"""
        workout = get_object_or_404(Workout, id=workout_id)
        
        context = {
            'workout': workout,
        }
        
        return render(request, 'meals/workout_detail.html', context)
        
    def delete_workout(request, workout_id):
        """View for deleting a workout"""
        workout = get_object_or_404(Workout, id=workout_id)
        
        if request.method == 'POST':
            workout.delete()
            messages.success(request, "Workout deleted successfully")
            return redirect('workout_home')
        
        return render(request, 'meals/delete_workout.html', {'workout': workout})
        
    def workout_presets(request):
        """View for managing workout presets"""
        presets = WorkoutPreset.objects.all().order_by('name')
        exercises = Exercise.objects.all().order_by('name')
        
        context = {
            'presets': presets,
            'exercises': exercises,
        }
        
        return render(request, 'meals/workout_presets.html', context)
    
    def create_workout_preset(request):
        """View for creating a new workout preset"""
        exercises = Exercise.objects.all().order_by('name')
        
        if request.method == 'POST':
            name = request.POST.get('preset_name')
            exercise_ids = request.POST.getlist('exercises')
            
            if not name:
                messages.error(request, "Preset name is required")
                return redirect('workout_presets')
                
            preset = WorkoutPreset.objects.create(name=name)
            
            # Add selected exercises to the preset with custom settings
            for i, exercise_id in enumerate(exercise_ids):
                try:
                    exercise = Exercise.objects.get(id=exercise_id)
                    
                    # Get custom settings for this exercise
                    default_sets = request.POST.get(f'sets_{exercise_id}', 3)
                    min_reps = request.POST.get(f'min_reps_{exercise_id}', 8)
                    max_reps = request.POST.get(f'max_reps_{exercise_id}', 12)
                    custom_name = request.POST.get(f'custom_name_{exercise_id}', '')
                    
                    # Create preset exercise with settings
                    PresetExercise.objects.create(
                        preset=preset,
                        exercise=exercise,
                        order=i+1,
                        default_sets=default_sets,
                        min_reps=min_reps,
                        max_reps=max_reps,
                        custom_name=custom_name
                    )
                except Exercise.DoesNotExist:
                    pass
            
            messages.success(request, f"Workout preset '{name}' created successfully")
            return redirect('workout_presets')
        
        return render(request, 'meals/create_workout_preset.html', {'exercises': exercises})
    
    def edit_workout_preset(request, preset_id):
        """View for editing a workout preset"""
        preset = get_object_or_404(WorkoutPreset, id=preset_id)
        all_exercises = Exercise.objects.all().order_by('name')
        preset_exercises = PresetExercise.objects.filter(preset=preset).order_by('order')
        
        if request.method == 'POST':
            name = request.POST.get('preset_name')
            exercise_ids = request.POST.getlist('exercises')
            
            if not name:
                messages.error(request, "Preset name is required")
                return redirect('edit_workout_preset', preset_id=preset_id)
                
            preset.name = name
            preset.save()
            
            # Remove existing preset exercises
            PresetExercise.objects.filter(preset=preset).delete()
            
            # Add selected exercises to the preset with custom settings
            for i, exercise_id in enumerate(exercise_ids):
                try:
                    exercise = Exercise.objects.get(id=exercise_id)
                    
                    # Get custom settings for this exercise
                    default_sets = request.POST.get(f'sets_{exercise_id}', 3)
                    min_reps = request.POST.get(f'min_reps_{exercise_id}', 8)
                    max_reps = request.POST.get(f'max_reps_{exercise_id}', 12)
                    custom_name = request.POST.get(f'custom_name_{exercise_id}', '')
                    
                    # Create preset exercise with settings
                    PresetExercise.objects.create(
                        preset=preset,
                        exercise=exercise,
                        order=i+1,
                        default_sets=default_sets,
                        min_reps=min_reps,
                        max_reps=max_reps,
                        custom_name=custom_name
                    )
                except Exercise.DoesNotExist:
                    pass
            
            messages.success(request, f"Workout preset '{name}' updated successfully")
            return redirect('workout_presets')
        
        context = {
            'preset': preset,
            'all_exercises': all_exercises,
            'preset_exercises': preset_exercises,
        }
        
        return render(request, 'meals/edit_workout_preset.html', context)
    
    def delete_workout_preset(request, preset_id):
        """View for deleting a workout preset"""
        preset = get_object_or_404(WorkoutPreset, id=preset_id)
        
        if request.method == 'POST':
            preset_name = preset.name
            preset.delete()
            messages.success(request, f"Workout preset '{preset_name}' deleted successfully")
            return redirect('workout_presets')
        
        return render(request, 'meals/delete_workout_preset.html', {'preset': preset})
        
    def exercise_progress(request, exercise_id=None):
        """View for seeing progress on exercises"""
        exercises = Exercise.objects.all().order_by('name')
        
        selected_exercise = None
        exercise_data = []
        
        if exercise_id:
            selected_exercise = get_object_or_404(Exercise, id=exercise_id)
            
            # Get all workout exercises for this exercise
            workout_exercises = WorkoutExercise.objects.filter(
                exercise=selected_exercise
            ).order_by('created_at')
            
            # Collect data for each workout
            for we in workout_exercises:
                sets = ExerciseSet.objects.filter(workout_exercise=we)
                
                if sets.exists():
                    for set_obj in sets:
                        # Convert all weights to kg for consistency
                        weight_kg = set_obj.weight
                        if set_obj.weight_unit == 'lb':
                            weight_kg = float(weight_kg) * 0.453592  # Convert lbs to kg
                            
                        # Calculate volume (weight x reps)
                        volume = weight_kg * set_obj.reps
                        
                        exercise_data.append({
                            'date': we.created_at.strftime('%Y-%m-%d'),
                            'set': set_obj.set_number,
                            'weight': float(weight_kg),
                            'reps': set_obj.reps,
                            'volume': float(volume),
                            'original_weight': float(set_obj.weight),
                            'weight_unit': set_obj.weight_unit
                        })
        
        context = {
            'exercises': exercises,
            'selected_exercise': selected_exercise,
            'exercise_data': json.dumps(exercise_data),
        }
        
        return render(request, 'meals/exercise_progress.html', context)

    def add_exercise_to_workout(request, workout_id):
        """API view for adding an exercise to a workout"""
        if request.method == 'POST':
            workout = get_object_or_404(Workout, id=workout_id)
            
            if not workout.is_active():
                return JsonResponse({'status': 'error', 'message': 'Cannot add exercise to a finished workout'})
            
            exercise_id = request.POST.get('exercise_id')
            
            if exercise_id:
                exercise = get_object_or_404(Exercise, id=exercise_id)
            else:
                exercise_name = request.POST.get('exercise_name')
                exercise_category = request.POST.get('exercise_category')
                
                if not exercise_name or not exercise_category:
                    return JsonResponse({'status': 'error', 'message': 'Exercise name and category are required'})
                
                exercise = Exercise.objects.create(
                    name=exercise_name,
                    category=exercise_category
                )
            
            # Get the order (highest existing order + 1)
            order = WorkoutExercise.objects.filter(workout=workout).count() + 1
            
            # Create the workout exercise
            workout_exercise = WorkoutExercise.objects.create(
                workout=workout,
                exercise=exercise,
                order=order
            )
            
            # Return the new workout exercise data
            return JsonResponse({
                'status': 'success',
                'workout_exercise_id': workout_exercise.id,
                'exercise_name': exercise.name,
                'exercise_category': exercise.category,
            })
        
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    def add_set_to_exercise(request, workout_exercise_id):
        """API view for adding a set to a workout exercise"""
        if request.method == 'POST':
            workout_exercise = get_object_or_404(WorkoutExercise, id=workout_exercise_id)
            
            # Check if the workout is active
            if not workout_exercise.workout.is_active():
                return JsonResponse({'status': 'error', 'message': 'Cannot add set to an exercise in a finished workout'})
            
            # Get the set data
            weight = request.POST.get('weight')
            weight_unit = request.POST.get('weight_unit', 'lb')
            reps = request.POST.get('reps')
            
            if not weight or not reps:
                return JsonResponse({'status': 'error', 'message': 'Weight and reps are required'})
            
            try:
                weight = float(weight)
                reps = int(reps)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid weight or reps format'})
            
            # Get the set number (highest existing set number + 1)
            set_number = ExerciseSet.objects.filter(workout_exercise=workout_exercise).count() + 1
            
            # Create the exercise set
            exercise_set = ExerciseSet.objects.create(
                workout_exercise=workout_exercise,
                set_number=set_number,
                weight=weight,
                weight_unit=weight_unit,
                reps=reps
            )
            
            # Return the new exercise set data
            return JsonResponse({
                'status': 'success',
                'set_id': exercise_set.id,
                'set_number': exercise_set.set_number,
                'weight': float(exercise_set.weight),
                'weight_unit': exercise_set.weight_unit,
                'reps': exercise_set.reps,
            })
        
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    def get_previous_exercise_data(request, exercise_id):
        """API view for getting previous exercise data"""
        exercise = get_object_or_404(Exercise, id=exercise_id)
        
        # Get the most recent workout exercise for this exercise
        previous_workout_exercise = WorkoutExercise.objects.filter(
            exercise=exercise
        ).order_by('-created_at').first()
        
        if not previous_workout_exercise:
            return JsonResponse({'status': 'success', 'has_previous': False})
        
        # Get the sets for this previous workout exercise
        previous_sets = ExerciseSet.objects.filter(workout_exercise=previous_workout_exercise)
        
        if not previous_sets:
            return JsonResponse({'status': 'success', 'has_previous': False})
        
        # Format the previous sets data
        previous_sets_data = []
        for set_obj in previous_sets:
            previous_sets_data.append({
                'set_number': set_obj.set_number,
                'weight': float(set_obj.weight),
                'weight_unit': set_obj.weight_unit,
                'reps': set_obj.reps,
            })
        
        return JsonResponse({
            'status': 'success',
            'has_previous': True,
            'previous_sets': previous_sets_data,
            'previous_date': previous_workout_exercise.created_at.strftime('%Y-%m-%d'),
        })
        
    def add_exercise(request):
        """API view for adding a new exercise"""
        if request.method == 'POST':
            name = request.POST.get('name')
            category = request.POST.get('category')
            
            if not name or not category:
                return JsonResponse({'status': 'error', 'message': 'Name and category are required'})
            
            # Create the exercise
            exercise = Exercise.objects.create(
                name=name,
                category=category
            )
            
            return JsonResponse({
                'status': 'success',
                'exercise_id': exercise.id,
                'name': exercise.name,
                'category': exercise.category
            })
        
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
def habit_home(request):
    """View for the habit tracking home page"""
    # Get the profile from the request or use the default profile
    profile_id = request.GET.get('profile')
    
    if profile_id:
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            profile = Profile.objects.first()
    else:
        profile = Profile.objects.first()
    
    # Create an initial profile if none exist
    if not profile:
        profile = Profile.objects.create(name="Default Profile")
    
    # Get all available profiles
    profiles = Profile.objects.all()
    
    # Get all habits for the selected profile
    habits = Habit.objects.filter(profile=profile).order_by('name')
    
    # Get today's date
    today = timezone.now().date()
    
    # Check which habits have been completed today
    for habit in habits:
        habit.completed_today = HabitCompletion.objects.filter(
            habit=habit, 
            completion_date=today
        ).exists()
    
    # Form for creating a new habit
    if request.method == 'POST':
        if 'create_habit' in request.POST:
            name = request.POST.get('habit_name', '').strip()
            description = request.POST.get('habit_description', '').strip()
            frequency = request.POST.get('habit_frequency', 'daily')
            
            if name:
                Habit.objects.create(
                    name=name,
                    description=description,
                    frequency=frequency,
                    profile=profile
                )
                return redirect('habit_home')
    
    context = {
        'habits': habits,
        'profiles': profiles,
        'selected_profile': profile,
        'today': today,
    }
    
    return render(request, 'meals/habit_home.html', context)

def toggle_habit_completion(request, habit_id):
    """Toggle the completion status of a habit for today"""
    if request.method == 'POST':
        habit = get_object_or_404(Habit, id=habit_id)
        today = timezone.now().date()
        
        # Check if already completed today
        completion = HabitCompletion.objects.filter(
            habit=habit,
            completion_date=today
        ).first()
        
        if completion:
            # If already completed, remove the completion
            completion.delete()
            status = 'uncompleted'
        else:
            # If not completed, add a completion
            HabitCompletion.objects.create(
                habit=habit,
                completion_date=today
            )
            status = 'completed'
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': status,
                'habit_id': habit_id,
                'message': f"Habit '{habit.name}' marked as {status}"
            })
        
        # For regular form submissions, redirect back to the habit home
        return redirect('habit_home')
    
    # For GET requests, redirect to habit home
    return redirect('habit_home')

def delete_habit(request, habit_id):
    """Delete a habit"""
    if request.method == 'POST':
        habit = get_object_or_404(Habit, id=habit_id)
        habit.delete()
        
        # For AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'deleted',
                'habit_id': habit_id,
                'message': f"Habit '{habit.name}' deleted"
            })
    
    return redirect('habit_home')

def edit_habit(request, habit_id):
    """Edit a habit"""
    habit = get_object_or_404(Habit, id=habit_id)
    
    if request.method == 'POST':
        name = request.POST.get('habit_name', '').strip()
        description = request.POST.get('habit_description', '').strip()
        frequency = request.POST.get('habit_frequency', 'daily')
        
        if name:
            habit.name = name
            habit.description = description
            habit.frequency = frequency
            habit.save()
            
            # For AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'updated',
                    'habit_id': habit_id,
                    'name': habit.name,
                    'description': habit.description,
                    'frequency': habit.frequency,
                    'message': f"Habit updated successfully"
                })
        
        return redirect('habit_home')
    
    context = {
        'habit': habit,
    }
    
    return render(request, 'meals/edit_habit.html', context)