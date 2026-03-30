from django.shortcuts import render,redirect
from django.views import View
from .forms import FacultyForm,FacultyInfoForm
from .models import FacultyInfo
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
import threading
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from student.views import EmailThread
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from questions.views import has_group
from django.utils import timezone

@login_required(login_url='faculty-login')
def index(request):
    from questions.models import Exam_Model
    from student.models import StudentInfo
    from django.utils import timezone

    # Get real data for the dashboard (only active exams)
    total_exams = Exam_Model.objects.filter(professor=request.user, is_active=True).count()
    total_students = StudentInfo.objects.count()
    completed_exams = Exam_Model.objects.filter(
        professor=request.user,
        is_active=True,
        end_time__lt=timezone.now()
    ).count()
    upcoming_exams = Exam_Model.objects.filter(
        professor=request.user,
        is_active=True,
        start_time__gt=timezone.now()
    ).count()

    # Get recent exams (last 5)
    recent_exams = Exam_Model.objects.filter(professor=request.user, is_active=True).order_by('-start_time')[:5]

    context = {
        'total_exams': total_exams,
        'total_students': total_students,
        'completed_exams': completed_exams,
        'upcoming_exams': upcoming_exams,
        'recent_exams': recent_exams,
    }

    return render(request, 'faculty/index.html', context)

class Register(View):
    def get(self,request):
        faculty_form = FacultyForm()
        faculty_info_form = FacultyInfoForm()
        return render(request,'faculty/register.html',{'faculty_form':faculty_form,'faculty_info_form':faculty_info_form})
    
    def post(self,request):
        faculty_form = FacultyForm(data=request.POST)
        faculty_info_form = FacultyInfoForm(data=request.POST)
        email = request.POST['email']

        if faculty_form.is_valid() and faculty_info_form.is_valid():
            faculty = faculty_form.save()
            faculty.set_password(faculty.password)
            faculty.is_active = True
            faculty.is_staff = True
            faculty.save()

            domain = get_current_site(request).domain
            email_subject = 'Activate your Exam Portal Faculty account'
            email_body = "Hi. Please contact the admin team of "+domain+". To register yourself as a professor."+ ".\n\n You are receiving this message because you registered on " + domain +". If you didn't register please contact support team on " + domain 
            fromEmail = settings.DEFAULT_FROM_EMAIL
            email = EmailMessage(
				email_subject,
				email_body,
				fromEmail,
				[email],
            )
            student_info = faculty_info_form.save(commit=False)
            student_info.user = faculty
            if 'picture' in request.FILES:
                student_info.picture = request.FILES['picture']
            student_info.save()
            messages.success(request,"Registered Succesfully. Check Email for confirmation")
            EmailThread(email).start()
            return redirect('faculty-login')
        else:
            print(faculty_form.errors,faculty_info_form.errors)
            return render(request,'faculty/register.html',{'faculty_form':faculty_form,'faculty_info_form':faculty_info_form})
    
class LoginView(View):
	def get(self,request):
		return render(request,'faculty/login.html')
	def post(self,request):
		username = request.POST['username']
		password = request.POST['password']
		has_grp = False
		if username and password:
			user = auth.authenticate(username=username,password=password)
			exis = User.objects.filter(username=username).exists()
			if exis:
				user_ch = User.objects.get(username=username)
				has_grp = has_group(user_ch,"Professor")
			if user and user.is_active and exis and has_grp:
				# NEW 2FA FLOW: Instead of directly logging in,
				# redirect to OTP verification page
				from core.two_factor_auth import TwoFactorAuth
				
				# Verify user has an email configured
				if not user.email:
					messages.error(request, "Your account does not have an email address configured. Please contact administrator to update your profile email.")
					return render(request, 'faculty/login.html')
				
				ip_address = self.get_client_ip(request)
				user_agent = request.META.get('HTTP_USER_AGENT', '')
				
				# Create OTP session
				session_result = TwoFactorAuth.create_otp_session(
					user_email=user.email,
					user=user,
					ip_address=ip_address,
					user_agent=user_agent,
				)
				
				if not session_result['success']:
					messages.error(request, "Failed to initiate 2FA. Please try again.")
					return render(request, 'faculty/login.html')
				
				# Send OTP email
				email_result = TwoFactorAuth.send_email_otp(
					session_id=session_result['session_id'],
					user_email=user.email,
					user_name=user.get_full_name() or user.username,
				)
				
				if not email_result['success']:
					messages.error(request, "Failed to send OTP. Please try again.")
					return render(request, 'faculty/login.html')
				
				# Redirect to OTP verification page
				import urllib.parse
				otp_url = f"/auth/otp/?session_id={session_result['session_id']}&email={urllib.parse.quote(user.email)}"
				return redirect(otp_url)
			elif not has_grp and exis:
				messages.error(request,'You dont have permssions to login as faculty. If You think this is a mistake please contact admin')	
				return render(request,'faculty/login.html')
                
			else:
				messages.error(request,'Invalid credentials')	
				return render(request,'faculty/login.html')
            
            

		messages.error(request,'Please fill all fields')
		return render(request,'faculty/login.html')

	@staticmethod
	def get_client_ip(request):
		"""Extract client IP address from request."""
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			ip = x_forwarded_for.split(',')[0]
		else:
			ip = request.META.get('REMOTE_ADDR')
		return ip

class LogoutView(View):
    def get(self, request):
        auth.logout(request)
        messages.success(request, 'Logged Out')
        return redirect('faculty-login')

    def post(self,request):
        auth.logout(request)
        messages.success(request,'Logged Out')
        return redirect('faculty-login')
