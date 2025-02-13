from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('daily_submission/', views.daily_submission_view, name='daily_submission'),
    path('submission_success/', views.submission_success, name='submission_success'),
    path('submissions/', views.submissions_list_view, name='submissions_list'),
    path('submission/<int:pk>/', views.submission_detail_view, name='submission_detail'),
    # Add other URL patterns here
]
