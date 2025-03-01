from django import forms
from .models import DailySubmission, Dish, AcneEntry, SkinProduct, RecipeTemplate, Profile, DailyCalorieGoal

class DailySubmissionForm(forms.ModelForm):
    class Meta:
        model = DailySubmission
        fields = ['dish', 'submission_date', 'notes', 'image', 'profile']  # Add 'image' to the fields

class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['cook_time', 'instructions']


class CalorieGoalRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    calorie_goal = forms.IntegerField(min_value=0, initial=0)
    profile = forms.ModelChoiceField(queryset=Profile.objects.all(), required=True)

class SkinProductForm(forms.ModelForm):
    class Meta:
        model = SkinProduct
        fields = ['name', 'brand', 'product_type']

class AcneEntryForm(forms.ModelForm):
    new_product = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Add new product name'
    }))
    new_product_brand = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Brand name (optional)'
    }))
    
    class Meta:
        model = AcneEntry
        fields = ['entry_date', 'severity', 'image', 'notes', 'products_used']
        widgets = {
            'entry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class RecipeTemplateForm(forms.ModelForm):
    class Meta:
        model = RecipeTemplate
        fields = ['name', 'base_calories', 'base_servings']

class ProfileSelectForm(forms.Form):
    profile = forms.ModelChoiceField(queryset=Profile.objects.all(), required=True, 
                                    widget=forms.Select(attrs={'class': 'profile-select'}))