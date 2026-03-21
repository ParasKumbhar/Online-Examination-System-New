"""
Middleware for security, audit logging, and rate limiting.
"""

import logging
import json
import hashlib
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from datetime import datetime, timedelta
from django.utils import timezone

security_logger = logging.getLogger('security')
app_logger = logging.getLogger('app')

class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Logs all critical actions for audit trail.
    """
    
    AUDIT_PATHS = [
        '/admin/',
        '/exams/',
        '/faculty/',
        '/student/',
    ]
    
    def process_request(self, request):
        """Log incoming request details."""
        request._audit_start_time = datetime.now()
        
        # Store request metadata
        request._ip_address = self.get_client_ip(request)
        request._user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        return None
    
    def process_response(self, request, response):
        """Log response and audit trail for sensitive operations."""
        
        # Only audit certain paths
        if not any(request.path.startswith(path) for path in self.AUDIT_PATHS):
            return response
        
        # Only audit POST, PUT, DELETE
        if request.method not in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return response
        
        # Skip non-sensitive endpoints
        if self.is_safe_endpoint(request.path):
            return response
        
        duration = (datetime.now() - request._audit_start_time).total_seconds()
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'user': str(request.user),
            'action': request.method,
            'path': request.path,
            'ip_address': getattr(request, '_ip_address', 'Unknown'),
            'user_agent': getattr(request, '_user_agent', 'Unknown'),
            'status_code': response.status_code,
            'duration_ms': int(duration * 1000),
        }
        
        # Log to audit file
        security_logger.info(json.dumps(audit_entry))
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')
    
    @staticmethod
    def is_safe_endpoint(path):
        """Check if endpoint is safe from audit logging."""
        safe_paths = [
            '/admin/login',
            '/student/login',
            '/faculty/login',
        ]
        return any(path.startswith(p) for p in safe_paths)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    
    def process_response(self, request, response):
        """Add security headers."""
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature policy / Permissions policy
        response['Permissions-Policy'] = (
            'accelerometer=(), camera=(), geolocation=(), '
            'gyroscope=(), magnetometer=(), microphone=(), '
            'payment=(), usb=()'
        )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting based on IP address.
    """
    
    RATE_LIMITS = {
        # 'login': (5, 300),  # DISABLED - was 5 attempts per 5 minutes
        'api': (100, 3600),  # 100 requests per hour
    }
    
    def process_request(self, request):
        """Check rate limits."""
        
        ip = self.get_client_ip(request)
        
        # Rate limit API endpoints only (login rate limiting DISABLED)
        # Disabled login rate limiting as per request
        
        if request.path.startswith('/api/'):
            return self.check_rate_limit(ip, 'api', request)
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    @staticmethod
    def check_rate_limit(identifier, limit_type, request):
        """Check if identifier has exceeded rate limit."""
        
        limit, window = RateLimitMiddleware.RATE_LIMITS.get(
            limit_type, (100, 3600)
        )
        
        cache_key = f'rate_limit:{limit_type}:{identifier}'
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            security_logger.warning(
                f'Rate limit exceeded: {identifier} on {limit_type}'
            )
            return JsonResponse(
                {'error': 'Rate limit exceeded. Try again later.'},
                status=429
            )
        
        # Increment counter
        cache.set(cache_key, current_count + 1, window)
        
        return None


class IPTrackingMiddleware(MiddlewareMixin):
    """
    Track IP addresses for security purposes.
    """
    
    def process_request(self, request):
        """Track user IP address."""
        
        if request.user.is_authenticated:
            ip = self.get_client_ip(request)
            
            # Store IP in session
            if 'user_ips' not in request.session:
                request.session['user_ips'] = []
            
            user_ips = request.session['user_ips']
            if ip not in user_ips:
                user_ips.append(ip)
                request.session['user_ips'] = user_ips[-5:]  # Keep last 5 IPs
                request.session.modified = True
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class DeviceFingerprinting(MiddlewareMixin):
    """
    Generate device fingerprint for security.
    """
    
    def process_request(self, request):
        """Generate or verify device fingerprint."""
        
        if request.user.is_authenticated:
            fingerprint = self.generate_fingerprint(request)
            request.device_fingerprint = fingerprint
            
            # Store in session for later comparison
            if 'device_fingerprint' not in request.session:
                request.session['device_fingerprint'] = fingerprint
        
        return None
    
    @staticmethod
    def generate_fingerprint(request):
        """Generate a device fingerprint."""
        
        components = [
            request.META.get('HTTP_USER_AGENT', ''),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('HTTP_ACCEPT_ENCODING', ''),
        ]
        
        fingerprint_str = '|'.join(components)
        fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()
        
        return fingerprint


class IPWhitelistMiddleware(MiddlewareMixin):
    """IP Whitelisting middleware."""
    
    def process_request(self, request):
        from core.models import IPWhitelist
        
        ip = self.get_client_ip(request)
        
        # Check admin/login/API auth paths
        protected_paths = ['/admin/', '/api/v1/auth/', '/api/v2/auth/']
        if any(request.path.startswith(p) for p in protected_paths):
            whitelisted_ips = list(IPWhitelist.objects.filter(is_active=True).values_list('ip_address', flat=True))
            if ip not in whitelisted_ips:
                security_logger.warning(f'IP not whitelisted: {ip} on {request.path}')
                from core.models import AuditLog
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='IP_BLOCKED',
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=False,
                    details={'path': request.path}
                )
                return JsonResponse({'error': 'Access denied: IP not whitelisted'}, status=403)
        
        request._client_ip = ip
        return None
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')


class SuspiciousLoginMiddleware(MiddlewareMixin):
    """Detect suspicious logins and log to audit. Triggers 2FA."""
    
    LOGIN_PATHS = ['/api/v1/auth/login/', '/api/v2/auth/login/', '/admin/login', '/student/login', '/faculty/login']
    
    def process_request(self, request):
        if any(request.path.startswith(p) for p in self.LOGIN_PATHS) and request.method == 'POST':
            ip = getattr(request, '_client_ip', self.get_client_ip(request))
            ua = request.META.get('HTTP_USER_AGENT', 'Unknown')
            fingerprint = getattr(request, 'device_fingerprint', 'unknown')
            
            is_suspicious = self.is_suspicious_login(request, ip, fingerprint)
            
            # Always log login attempt
            from core.models import LoginAudit
            audit = LoginAudit.objects.create(
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip,
                user_agent=ua,
                device_fingerprint=fingerprint,
                success=False,  # Updated post-auth
                suspicious=is_suspicious,
                reason='New IP/device/location' if is_suspicious else 'Normal login'
            )
            
            if is_suspicious and request.user.is_authenticated:
                # Trigger 2FA for suspicious logins
                from core.two_factor_auth import TwoFactorAuth
                TwoFactorAuth.require_2fa_verification(request.user)
                audit.reason += '; 2FA required'
                audit.save()
                security_logger.warning(f'Suspicious login detected for {request.user}: {ip} - 2FA triggered')
            
            request._login_audit_id = audit.id
            request._login_audit_suspicious = is_suspicious
        
        return None
    
    def is_suspicious_login(self, request, ip, fingerprint):
        user_ips = request.session.get('user_ips', [])
        session_fp = request.session.get('device_fingerprint')
        
        # New IP or device
        is_new_ip = ip not in user_ips
        is_new_device = fingerprint != session_fp
        
        # Multiple failed attempts from same IP (check recent audits)
        from core.models import LoginAudit
        recent_fails = LoginAudit.objects.filter(
            ip_address=ip, success=False
        ).filter(timestamp__lt=datetime.now(),
            timestamp__gte=datetime.now() - timedelta(minutes=15)
        ).count()
        
        return is_new_ip or is_new_device or recent_fails > 3
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')

