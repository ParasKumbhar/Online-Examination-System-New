from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest

def index(request):
    return render(request,'homepage.html')


@require_http_methods(["GET"])
def otp_verification(request):
    """
    OTP Verification Page
    GET /auth/otp/?session_id=xxx&email=user@example.com
    
    This page is shown after successful credential verification.
    User enters 6-digit OTP received via email.
    """
    session_id = request.GET.get('session_id')
    email = request.GET.get('email')
    
    # Validate parameters
    if not session_id or not email:
        return HttpResponseBadRequest('Missing session_id or email parameter')
    
    # Verify session exists
    try:
        from core.models import OTPSession
        otp_session = OTPSession.objects.get(session_id=session_id, is_active=True)
        
        # Verify email matches
        if otp_session.user_email != email:
            return HttpResponseBadRequest('Session email mismatch')
        
        # Check if already verified
        if otp_session.otp_verified:
            return HttpResponseBadRequest('OTP already verified')
        
        # Check if expired
        if otp_session.is_expired():
            return HttpResponseBadRequest('OTP session has expired')
    
    except OTPSession.DoesNotExist:
        return HttpResponseBadRequest('OTP session not found')
    
    context = {
        'session_id': session_id,
        'email': email,
        'expires_in_minutes': 3,  # Default OTP expiry
        'user': otp_session.user,  # Pass user object for avatar display
    }
    
    return render(request, 'auth/otp_verification.html', context)


@require_http_methods(["GET"])
def avatar_showcase(request):
    """
    Avatar Component Showcase
    Displays all avatar sizes and use cases
    """
    return render(request, 'components_showcase.html')