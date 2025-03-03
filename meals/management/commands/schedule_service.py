from django.core.management.base import BaseCommand
from django.utils import timezone
import os
import subprocess

class Command(BaseCommand):
    help = 'Manage service schedule'

    def handle(self, *args, **kwargs):
        current_time = timezone.now().time()
        
        if current_time.hour == 0 and current_time.minute == 0:
            subprocess.run(["railway", "stop"])
        
        if current_time.hour == 7 and current_time.minute == 0:
            subprocess.run(["railway", "start"])