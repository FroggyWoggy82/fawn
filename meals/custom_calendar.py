# custom_calendar.py
import calendar
from datetime import date

class CustomHTMLCalendar(calendar.HTMLCalendar):
    def __init__(self, year, month, day_data):
        """
        day_data: dict mapping date objects to (calories_eaten, calorie_goal)
        """
        self.year = year
        self.month = month
        self.day_data = day_data
        super().__init__()

    def formatday(self, day, weekday):
        if day == 0:
            # Day outside current month; we return an empty cell.
            return '<td class="noday">&nbsp;</td>'
        current_date = date(self.year, self.month, day)
        # Get the aggregated calories and goal (default 0 if not set)
        eaten, goal = self.day_data.get(current_date, (0, 0))
        cell_content = f"""
            <div class="day-header">{day}</div>
            <div class="calorie-info">{eaten}/{goal}</div>
        """
        # Highlight today's cell
        if current_date == date.today():
            return f'<td class="calendar-day calendar-today">{cell_content}</td>'
        else:
            return f'<td class="calendar-day">{cell_content}</td>'

    def formatweek(self, theweek):
        week_html = "".join(self.formatday(d, wd) for (d, wd) in theweek)
        return f"<tr>{week_html}</tr>"

    def formatmonth(self, withyear=True):
        html = []
        html.append('<table class="calendar-table">')
        html.append(self.formatmonthname(self.year, self.month, withyear=withyear))
        html.append(self.formatweekheader())
        for week in self.monthdays2calendar(self.year, self.month):
            html.append(self.formatweek(week))
        html.append('</table>')
        return ''.join(html)
