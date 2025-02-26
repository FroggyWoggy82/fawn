from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('daily_submission/', views.daily_submission_view, name='daily_submission'),
    path('submission_success/', views.submission_success, name='submission_success'),
    path('get_ingredients/<int:dish_id>/', views.get_ingredients, name='get_ingredients'),
    path('submissions/', views.submissions_list_view, name='submissions_list'),
    path('submission/<int:pk>/', views.submission_detail_view, name='submission_detail'),
    path('submission_view/<int:submission_id>/', views.submission_view, name='submission_view'),
    path('submission/delete/<int:submission_id>/', views.delete_submission, name='delete_submission'),
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Adding the dashboard URL pattern
]
