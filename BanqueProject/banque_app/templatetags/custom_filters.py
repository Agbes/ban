from django import template

register = template.Library()

@register.filter
def custom_filter(value):
    # Your filter logic here
    return value*20


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return None