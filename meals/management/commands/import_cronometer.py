from django.core.management.base import BaseCommand
from meals.models import DailySubmissionIngredient

class Command(BaseCommand):
    help = 'Update cost_per_gram for existing DailySubmissionIngredient records'

    def handle(self, *args, **kwargs):
        ingredients = DailySubmissionIngredient.objects.all()
        for ingredient in ingredients:
            ingredient.cost_per_gram = ingredient.dish_ingredient.ingredient.cost_per_gram
            ingredient.save()
        self.stdout.write(self.style.SUCCESS('Successfully updated cost_per_gram for all DailySubmissionIngredient records'))