# INTEGRATION CHECKLIST - PHASE 1 & 2 IMPLEMENTATION

## Complete this checklist to integrate all delivered code

---

## ✅ STEP 1: Environment Setup (30 min)

- [ ] Copy `.env.example` to `.env`
- [ ] Generate new SECRET_KEY:
  ```bash
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  ```
- [ ] Add SECRET_KEY to `.env`
- [ ] Set DEBUG=False in `.env` (for testing)
- [ ] Add email credentials to `.env`
- [ ] Save `.env` file (DO NOT COMMIT)
- [ ] Add `.env` to `.gitignore` (if not already there)

---

## ✅ STEP 2: Backup Current Settings (5 min)

- [ ] Backup current `Exam/examProject/settings.py`:
  ```bash
  cp Exam/examProject/settings.py Exam/examProject/settings.py.backup
  ```
- [ ] Store backup in safe location

---

## ✅ STEP 3: Install Dependencies (10 min)

```bash
pip install python-dotenv==0.21.0
pip install djangorestframework==3.14.0
pip install djangorestframework-simplejwt==5.2.2
pip install django-cors-headers==4.0.0
pip install django-redis==5.2.0
pip install django-filter==23.1
pip install psycopg2-binary==2.9.6
pip install python-json-logger==2.0.7
```

- [ ] Verify installations:
  ```bash
  pip list | grep -E "rest|cors|redis"
  ```

---

## ✅ STEP 4: Update Django Settings (10 min)

**Option A: Replace Entirely (Recommended)**
```bash
mv Exam/examProject/settings.py Exam/examProject/settings_old.py
mv Exam/examProject/settings_new.py Exam/examProject/settings.py
```

**Option B: Manual Merge (If you have custom settings)**
- [ ] Copy relevant sections from `settings_new.py` into existing `settings.py`
- [ ] Keep your custom configurations
- [ ] Update INSTALLED_APPS with new apps:
  ```python
  INSTALLED_APPS = [
      # ... existing apps ...
      'rest_framework',
      'rest_framework.authtoken',
      'corsheaders',
      'django_filter',
      'api',
      'notifications',
      'core',  # New
  ]
  ```

- [ ] Update MIDDLEWARE with new middleware:
  ```python
  MIDDLEWARE = [
      'django.middleware.security.SecurityMiddleware',
      'corsheaders.middleware.CorsMiddleware',  # NEW
      # ... rest of middleware ...
      'core.middleware.AuditLoggingMiddleware',  # NEW
      'core.middleware.SecurityHeadersMiddleware',  # NEW
      'core.middleware.RateLimitMiddleware',  # NEW
  ]
  ```

- [ ] Add REST_FRAMEWORK config (from settings_new.py)
- [ ] Add SIMPLE_JWT config (from settings_new.py)
- [ ] Add CORS config (from settings_new.py)
- [ ] Add CACHES config (from settings_new.py)
- [ ] Add LOGGING config (from settings_new.py)

---

## ✅ STEP 5: Update URLs (5 min)

Edit `Exam/examProject/urls.py`:

```python
# Add to urlpatterns:
path('api/', include('api.urls')),

# Example final file:
from django.contrib import admin
from . import views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('student/', include('student.urls')),
    path('faculty/', include('faculty.urls')),
    path('student-pref/', include('studentPreferences.urls')),
    path('exams/', include('questions.urls')),
    path('api/', include('api.urls')),  # NEW
    path('', views.index, name="homepage")
]

from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] Verify syntax: `python Exam/manage.py check`

---

## ✅ STEP 6: Create Logs Directory (2 min)

```bash
mkdir -p Exam/logs
touch Exam/logs/exam_system.log
touch Exam/logs/security.log
```

- [ ] Verify:
  ```bash
  ls -la Exam/logs/
  ```

---

## ✅ STEP 7: Run Migrations (10 min)

```bash
cd Exam

# Create migrations for new apps
python manage.py makemigrations core
python manage.py makemigrations notifications
python manage.py makemigrations api

# Run all migrations
python manage.py migrate

# Create superuser if needed
python manage.py createsuperuser
```

- [ ] No errors in migration output
- [ ] All migrations applied successfully

---

## ✅ STEP 8: Collect Static Files (5 min)

```bash
cd Exam
python manage.py collectstatic --noinput
```

- [ ] Verify static files collected

---

## ✅ STEP 9: Test Basics (15 min)

**Test 1: Server starts**
```bash
cd Exam
python manage.py runserver
# Should see "Starting development server at http://127.0.0.1:8000/"
```

- [ ] Server starts without errors
- [ ] Access http://localhost:8000/ - should see homepage

**Test 2: Admin site**
- [ ] Access http://localhost:8000/admin/
- [ ] Login with superuser credentials
- [ ] Should see new models: Notifications, NotificationPreferences, NotificationLog

**Test 3: API endpoints**
- [ ] Try GET http://localhost:8000/api/v1/exams/
  - Without auth: Should return 401 Unauthorized
  - With JWT token: Should return exam list

---

## ✅ STEP 10: Setup Redis (Optional but Recommended)

**Windows:**
- [ ] Download from: https://github.com/microsoftarchive/redis/releases
- [ ] Install and start Redis service

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**Test Redis:**
```bash
redis-cli ping
# Should return: PONG
```

- [ ] Redis server running and accessible

---

## ✅ STEP 11: 2FA Integration (Intermediate)

1. Update login views to check for 2FA:

**In `Exam/student/views.py` - LoginView.post():**

```python
from core.two_factor_auth import TwoFactorAuth, OTPGenerator

def post(self, request):
    username = request.POST['username']
    password = request.POST['password']
    
    user = auth.authenticate(username=username, password=password)
    
    if user and user.is_active:
        # Check if 2FA is enabled
        if TwoFactorAuth.is_2fa_enabled(user):
            # Send OTP
            result = OTPGenerator.send_email_otp(user.email, user.first_name)
            if result['success']:
                # Redirect to 2FA verification page
                request.session['pending_user_id'] = user.id
                return redirect('verify-otp')  # Create this view
        else:
            # Regular login
            auth.login(request, user)
            return redirect('index')
```

2. Create 2FA verification view:

```python
# In student/views.py
class VerifyOTPView(View):
    def get(self, request):
        return render(request, 'student/verify-otp.html')
    
    def post(self, request):
        user_id = request.session.get('pending_user_id')
        otp = request.POST.get('otp')
        
        user = User.objects.get(id=user_id)
        result = OTPGenerator.verify_otp(user.email, otp)
        
        if result['valid']:
            auth.login(request, user)
            del request.session['pending_user_id']
            return redirect('index')
        else:
            return render(request, 'student/verify-otp.html', 
                         {'error': result['message']})
```

- [ ] 2FA integration tested

---

## ✅ STEP 12: API Testing (20 min)

Use curl or Postman to test:

**Test Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

Expected response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

- [ ] Login endpoint working
- [ ] JWT tokens returned

**Test Exams:**
```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/v1/exams/
```

- [ ] Exams endpoint accessible with token
- [ ] Returns exam list

**Test Rate Limiting:**
```bash
# Make 6 login attempts rapidly
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username": "test", "password": "wrong"}'
done
```

- [ ] 6th request returns 429 Too Many Requests

---

## ✅ STEP 13: Verify Security Headers (10 min)

```bash
curl -I http://localhost:8000/

# Should see headers like:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
```

- [ ] Security headers present in response

---

## ✅ STEP 14: Check Logging (5 min)

```bash
cat Exam/logs/exam_system.log
cat Exam/logs/security.log
```

- [ ] Log files being written
- [ ] JSON format entries visible
- [ ] No obvious errors

---

## ✅ STEP 15: Documentation Review (10 min)

- [ ] Read [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- [ ] Read [AUDIT_REPORT.md](AUDIT_REPORT.md)
- [ ] Read [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
- [ ] Understand Phase 3 and Phase 4 requirements

---

## ⚠️ TROUBLESHOOTING

### Error: "ModuleNotFoundError: No module named 'rest_framework'"
```bash
pip install djangorestframework
```

### Error: "redis.exceptions.ConnectionError"
- Redis not running. Start Redis server
- Or set cache backend to database:
  ```python
  CACHES = {'default': {'BACKEND': 'django.core.cache.backends.db.DatabaseCache'}}
  ```

### Error: "No module named 'core'"
- Make sure `core` app is created in `INSTALLED_APPS`
- Create `Exam/core/__init__.py`

### Error in migrations
```bash
python manage.py migrate --plan  # See what will be applied
python manage.py migrate --fake-initial  # Skip initial migrations
```

### Settings file syntax error
```bash
python -m py_compile Exam/examProject/settings.py
```

---

## 📋 FINAL VERIFICATION CHECKLIST

- [ ] `.env` file created and configured
- [ ] Dependencies installed
- [ ] Settings.py updated or replaced
- [ ] URLs updated with API routes
- [ ] Logs directory created
- [ ] Migrations created and applied
- [ ] Static files collected
- [ ] Server starts without errors
- [ ] Admin site accessible
- [ ] API endpoints responding
- [ ] JWT tokens working
- [ ] Rate limiting functional
- [ ] Security headers present
- [ ] Logging working
- [ ] Documentation reviewed

---

## 🎯 NEXT STEPS

After completing this checklist:

1. **Week 1**: Test all endpoints comprehensively
2. **Week 2**: Setup PostgreSQL database
3. **Week 3**: Create test suite (50+ tests)
4. **Week 4**: Load testing and optimization

See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) Phase 3 & 4 for detailed next steps.

---

## ✅ INTEGRATION COMPLETE!

Once all checkboxes are marked ✅, you're ready for Phase 3 (Testing & Deployment).

**Estimated Time**: 2-3 hours for experienced Django developer

**Support**: Check implementation guide for detailed explanations

---

Generated: February 2, 2024  
Status: READY FOR IMPLEMENTATION
