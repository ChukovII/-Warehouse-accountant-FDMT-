from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(value, days):
    """Добавить дни к дате"""
    if value:
        return value + timedelta(days=int(days))
    return None

@register.filter
def timeuntil(date1, date2):
    """Разница между датами в днях"""
    if date1 and date2:
        return (date1 - date2).days
    return None