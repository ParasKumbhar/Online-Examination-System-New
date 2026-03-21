"""
Security & Authentication API Serializers
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from core.two_factor_auth import OTPGenerator, TwoFactorAuth
from core.models import LoginAudit
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JWTSerializerBase
import logging

logger = logging.getLogger('app')

class LoginSerializer(serializers.Serializer):
    """Serializer for user login with 2FA support."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

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
    """Serializer for requesting OTP."""
    email = serializers.EmailField()

    def validate_email(self, value):
        # Verify user exists with this email
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError('No active account found with this email')
        return value

class OTPVerifySerializer(serializers.Serializer):
    """Serializer for verifying OTP."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class JWTSerializer:
    """Custom JWT serializer with additional user info."""
    @classmethod
    def get_token(cls, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['groups'] = [g.name for g in user.groups.all()]
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

