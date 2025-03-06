from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', views.home_view, name='home'),
    path('daily_submission/', views.daily_submission_view, name='daily_submission'),
    path('submission_success/', views.submission_success, name='submission_success'),
    path('get_ingredients/<int:dish_id>/', views.get_ingredients, name='get_ingredients'),
    path('submissions/', views.submissions_list_view, name='submissions_list'),
    path('submission/<int:pk>/', views.submission_detail_view, name='submission_detail'),
    path('submission_view/<int:submission_id>/', views.submission_view, name='submission_view'),
    path('submission/delete/<int:submission_id>/', views.delete_submission, name='delete_submission'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('wir/', views.wir_view, name='wir_view'),
    path('acne/', views.acne_home, name='acne_home'),
    path('acne/new/', views.acne_entry_create, name='acne_entry_create'),
    path('acne/history/', views.acne_history, name='acne_history'),
    path('acne/entry/<int:entry_id>/', views.acne_entry_detail, name='acne_entry_detail'),
    path('acne/products/', views.product_analysis, name='product_analysis'),
    path('meal-planner/', views.meal_planner_view, name='meal_planner'),
    path('generate-grocery-list/', views.generate_grocery_list, name='generate_grocery_list'),
    path('dish-calculator/', views.dish_calculator_view, name='dish_calculator'),
    path('calculate-dish/', views.calculate_dish, name='calculate_dish'),
    path('workout/', views.workout_home, name='workout_home'),
    path('workout/start/', views.start_workout, name='start_workout'),
    path('workout/<int:workout_id>/', views.active_workout, name='active_workout'),
    path('workout/<int:workout_id>/finish/', views.finish_workout, name='finish_workout'),
    path('workout/<int:workout_id>/detail/', views.workout_detail, name='workout_detail'),
    path('workout/<int:workout_id>/delete/', views.delete_workout, name='delete_workout'),
    path('workout/<int:workout_id>/add-exercise/', views.add_exercise_to_workout, name='add_exercise_to_workout'),
    path('workout-exercise/<int:workout_exercise_id>/add-set/', views.add_set_to_exercise, name='add_set_to_exercise'),
    path('exercise/<int:exercise_id>/previous-data/', views.get_previous_exercise_data, name='get_previous_exercise_data'),
    path('workout/presets/', views.workout_presets, name='workout_presets'),
    path('workout/presets/create/', views.create_workout_preset, name='create_workout_preset'),
    path('workout/presets/<int:preset_id>/edit/', views.edit_workout_preset, name='edit_workout_preset'),
    path('workout/presets/<int:preset_id>/delete/', views.delete_workout_preset, name='delete_workout_preset'),
    path('exercise/progress/', views.exercise_progress, name='exercise_progress'),
    path('exercise/<int:exercise_id>/progress/', views.exercise_progress, name='exercise_specific_progress'),
    path('api/weight/', views.weight_api, name='weight_api'),
    path('weights/', views.weight_list, name='weight_list'),
    path('exercise/add/', views.add_exercise, name='add_exercise'),
    path('habits/', views.habit_home, name='habit_home'),
    path('habits/toggle/<int:habit_id>/', views.toggle_habit_completion, name='toggle_habit'),
    path('habits/delete/<int:habit_id>/', views.delete_habit, name='delete_habit'),
    path('habits/edit/<int:habit_id>/', views.edit_habit, name='edit_habit'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('api/notifications/<int:notification_id>/', views.get_notification, name='get_notification'),
    path('api/notifications/create/', views.create_notification, name='create_notification'),
    path('api/notifications/<int:notification_id>/update/', views.update_notification, name='update_notification'),
    path('api/notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('api/notifications/<int:notification_id>/test/', views.test_notification, name='test_notification'),
    path('service-worker.js', RedirectView.as_view(url=settings.STATIC_URL + 'service-worker.js'), name='service-worker'),
    
] 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)