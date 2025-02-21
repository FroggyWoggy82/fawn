from django import forms
from .models import DailySubmission, Dish

class DailySubmissionForm(forms.ModelForm):
    class Meta:
        model = DailySubmission
        fields = ['dish', 'submission_date', 'notes', 'image']  # Add 'image' to the fields

class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['cook_time', 'instructions']
