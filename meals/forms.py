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


class CalorieGoalRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    calorie_goal = forms.IntegerField(min_value=0, initial=0)
