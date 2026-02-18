from django import template

register = template.Library()


@register.filter
def primary_group(user):
    """Return the name of the first group for the user, or empty string."""
    if not hasattr(user, 'groups'):
        return ''
    try:
        g = user.groups.first()
        return g.name if g else ''
    except Exception:
        return ''


@register.filter
def in_group(user, group_name):
    """Return True if the user belongs to the given group name."""
    if not hasattr(user, 'groups'):
        return False
    try:
        return user.groups.filter(name=group_name).exists()
    except Exception:
        return False
