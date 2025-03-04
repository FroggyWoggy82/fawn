from django import template
import datetime

register = template.Library()

@register.filter
def time_format(seconds):
    """Format seconds into HH:MM:SS format"""
    try:
        seconds = int(float(seconds))
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
        return "00:00:00"

@register.filter
def filter_by_day(tasks, day_name):
    """Filter tasks by day of the week"""
    filtered_tasks = []
    for task in tasks:
        if hasattr(task, 'date') and task.date and task.date.strftime('%A') == day_name:
            filtered_tasks.append(task)
    return filtered_tasks