#!/bin/bash
gunicorn mealplanner.wsgi:application --bind 0.0.0.0:8000
