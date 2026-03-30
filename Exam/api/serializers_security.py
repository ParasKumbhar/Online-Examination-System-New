"""
Security & Authentication API Serializers
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from core.two_factor_auth import OTPGenerator, TwoFactorAuth
from core.models import LoginAudit, OTPSession
import logging

logger = logging.getLogger('app')

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Step 1 of 2FA flow: Validate credentials.
    
    Does NOT issue tokens here. Initiates OTP flow instead.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    device_fingerprint = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Both username and password are required')


class OTPRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting new OTP (resend).
    Used only for resending OTP after login step.
    """
    session_id = serializers.CharField()

    def validate_session_id(self, value):
        # Verify session exists
        if not OTPSession.objects.filter(session_id=value, is_active=True).exists():
            raise serializers.ValidationError('OTP session not found or expired')
        return value


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying OTP.
    Step 2 of 2FA flow: Verify OTP and get JWT tokens.
    """
    session_id = serializers.CharField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_otp(self, value):
        # Validate OTP format (6 digits)
        if not value.isdigit():
            raise serializers.ValidationError('OTP must be 6 digits')
        return value


class JWTSerializer:
    """Custom JWT serializer with additional user info."""
    @classmethod
    def get_token(cls, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['groups'] = [g.name for g in user.groups.all()]
        refresh['is_staff'] = user.is_staff
        return refresh


class LoginAuditSerializer(serializers.ModelSerializer):
    """Serializer for login audit logs."""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = LoginAudit
        fields = [
            'id', 'user', 'user_username', 'ip_address', 'user_agent',
            'device_fingerprint', 'success', 'suspicious', 'reason', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

