from django import template
from django.utils.html import mark_safe

register = template.Library()

# Google-inspired color palette for letter avatars
AVATAR_COLORS = {
    'A': '#EA4335', 'B': '#4285F4', 'C': '#34A853', 'D': '#FBBC04',
    'E': '#EA4335', 'F': '#34A853', 'G': '#4285F4', 'H': '#FBBC04',
    'I': '#EA4335', 'J': '#34A853', 'K': '#4285F4', 'L': '#FBBC04',
    'M': '#EA4335', 'N': '#34A853', 'O': '#4285F4', 'P': '#FBBC04',
    'Q': '#EA4335', 'R': '#34A853', 'S': '#4285F4', 'T': '#FBBC04',
    'U': '#EA4335', 'V': '#34A853', 'W': '#4285F4', 'X': '#FBBC04',
    'Y': '#EA4335', 'Z': '#34A853',
}


@register.filter
def get_avatar_color(text):
    """Get a color based on the first letter of text."""
    if not text:
        return '#4f46e5'  # Default indigo color
    first_letter = text[0].upper()
    return AVATAR_COLORS.get(first_letter, '#4f46e5')


@register.filter
def get_avatar_initials(user):
    """Get initials from user's first and last name."""
    if not user:
        return '?'
    if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
        first = user.first_name[0] if user.first_name else ''
        last = user.last_name[0] if user.last_name else ''
        initials = (first + last).upper()
        return initials if initials else user.username[0].upper()
    return user.username[0].upper() if user.username else '?'


@register.filter
def get_avatar_letter(user):
    """Get first letter from user's name."""
    if not user:
        return '?'
    if hasattr(user, 'first_name') and user.first_name:
        return user.first_name[0].upper()
    if hasattr(user, 'username') and user.username:
        return user.username[0].upper()
    return '?'


@register.inclusion_tag('partials/avatar.html')
def user_avatar(user, size='md', show_name=False):
    """
    Render user avatar with image fallback to letter.
    
    Args:
        user: User object
        size: 'sm' (32px), 'md' (48px), 'lg' (64px), 'xl' (96px)
        show_name: Boolean to show user's name next to avatar
    """
    # Try to get profile picture from StudentInfo
    profile_pic = None
    try:
        from student.models import StudentInfo
        student_info = StudentInfo.objects.get(user=user)
        if student_info.picture:
            profile_pic = student_info.picture.url
    except:
        pass
    
    # Fallback to admission profile_pic
    if not profile_pic:
        try:
            from admission.models import Admission
            admission = Admission.objects.filter(user=user).first()
            if admission and admission.profile_pic:
                profile_pic = admission.profile_pic.url
        except:
            pass
    
    # Get user's display name
    display_name = user.get_full_name() if hasattr(user, 'get_full_name') else user.username
    if not display_name.strip():
        display_name = user.username
    
    # Get letter for fallback
    letter = get_avatar_letter(user)
    color = get_avatar_color(letter)
    
    size_map = {
        'sm': {'wrapper': 'w-8 h-8 text-xs', 'image': 'w-8 h-8'},
        'md': {'wrapper': 'w-12 h-12 text-base', 'image': 'w-12 h-12'},
        'lg': {'wrapper': 'w-16 h-16 text-lg', 'image': 'w-16 h-16'},
        'xl': {'wrapper': 'w-24 h-24 text-2xl', 'image': 'w-24 h-24'},
    }
    
    return {
        'user': user,
        'profile_pic': profile_pic,
        'letter': letter,
        'color': color,
        'display_name': display_name,
        'size': size,
        'size_classes': size_map.get(size, size_map['md']),
        'show_name': show_name,
    }


@register.filter
def initials(user):
    """Get initials from user for avatar display."""
    if not user:
        return '?'
    first = (user.first_name[0] if user.first_name else '')
    last = (user.last_name[0] if user.last_name else '')
    initials_str = (first + last).upper()
    return initials_str if initials_str else user.username[0].upper()
