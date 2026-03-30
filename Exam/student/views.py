from django.shortcuts import render,redirect
from django.views import View
from .forms import StudentForm, StudentInfoForm
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode 
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from .utils import account_activation_token
from django.core.mail import EmailMessage
from django.conf import settings
import threading
from django.contrib.auth.models import User
from studentPreferences.models import StudentPreferenceModel
from django.contrib.auth.models import Group
from student.models import StuExam_DB, StuResults_DB

@login_required(login_url='login')
def index(request):
    from questions.models import Exam_Model
    from questions.exam_assignment_models import ExamAssignment
    from django.utils import timezone
    from django.db.models import Avg, Sum

    student = request.user
    now = timezone.localtime()

    # Ensure stored times are timezone-aware and converted to local timezone
    def _ensure_local(dt):
        if not dt:
            return dt
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_default_timezone())
        return timezone.localtime(dt)

    # Get ALL active exams - filter by assignments
    all_exams = Exam_Model.objects.filter(is_active=True).order_by('start_time')

    # Filter exams that student has access to
    accessible_exams = []
    for exam in all_exams:
        if ExamAssignment.is_exam_assigned_to_student(exam, student):
            accessible_exams.append(exam)

    # Filter out exams that the student has already completed
    upcoming_exams = []
    for exam in accessible_exams:
        stu_exam_record = StuExam_DB.objects.filter(
            student=student,
            examname=exam.name,
            qpaper=exam.question_paper
        ).first()

        # If student has already completed this exam, skip it (don't show in upcoming)
        if stu_exam_record and stu_exam_record.completed == 1:
            continue

        # Ensure exam datetime is timezone-aware and localised
        exam.start_time = _ensure_local(exam.start_time)
        exam.end_time = _ensure_local(exam.end_time)

        # Auto-mark as missed (0 score) if exam window has passed and the student never attempted
        if exam.end_time and now > exam.end_time:
            if not stu_exam_record:
                stu_exam_record = StuExam_DB.objects.create(
                    student=student,
                    examname=exam.name,
                    qpaper=exam.question_paper,
                    score=0,
                    completed=1
                )
            else:
                stu_exam_record.completed = 1
                stu_exam_record.score = stu_exam_record.score or 0
                stu_exam_record.save()
            results = StuResults_DB.objects.get_or_create(student=student)[0]
            if stu_exam_record not in results.exams.all():
                results.exams.add(stu_exam_record)
            continue

        # If it's still upcoming or active, show it as upcoming
        upcoming_exams.append(exam)
    
    # Get completed exams for this student
    completed_exams = StuExam_DB.objects.filter(student=student, completed=1)
    
    # Calculate average score from completed exams based on actual total marks
    avg_score_percent = "0%"
    if completed_exams.exists():
        total_marks_obtained = 0
        total_possible_marks = 0
        
        for exam_record in completed_exams:
            if exam_record.qpaper:
                for q in exam_record.qpaper.questions.all():
                    total_possible_marks += q.max_marks
        
        total_score_result = completed_exams.aggregate(total_score=Sum('score'))
        total_marks_obtained = total_score_result['total_score'] or 0
        
        if total_possible_marks > 0:
            percentage = (total_marks_obtained / total_possible_marks) * 100
            avg_score_percent = f"{int(percentage)}%"
    
    # Calculate rank
    all_students_scores = {}
    students_with_exams = StuExam_DB.objects.filter(completed=1).values_list('student_id', flat=True).distinct()
    for student_id in students_with_exams:
        student_exams = StuExam_DB.objects.filter(student_id=student_id, completed=1)
        
        student_total_obtained = 0
        student_total_possible = 0
        
        for exam_record in student_exams:
            if exam_record.qpaper:
                for q in exam_record.qpaper.questions.all():
                    student_total_possible += q.max_marks
        
        student_score_result = student_exams.aggregate(total_score=Sum('score'))
        student_total_obtained = student_score_result['total_score'] or 0
        
        if student_total_possible > 0:
            student_percentage = (student_total_obtained / student_total_possible) * 100
        else:
            student_percentage = 0
        
        all_students_scores[student_id] = student_percentage
    
    sorted_students = sorted(all_students_scores.items(), key=lambda x: x[1], reverse=True)
    
    rank = 'N/A'
    for i, (student_id, percentage) in enumerate(sorted_students, 1):
        if student_id == student.id:
            rank = i
            break
    
    context = {
        'upcoming_exams': upcoming_exams,
        'completed_exams': completed_exams,
        'avg_score': avg_score_percent,
        'rank': rank,
        'now': now,
    }
    
    return render(request,'student/index.html', context)

class Register(View):
    def get(self,request):
        student_form = StudentForm()
        student_info_form = StudentInfoForm()
        return render(request,'student/register.html',{'student_form':student_form,'student_info_form':student_info_form})
    
    def post(self,request):
        student_form = StudentForm(data=request.POST)
        student_info_form = StudentInfoForm(data=request.POST)
        email = request.POST['email']

        if student_form.is_valid() and student_info_form.is_valid():
            student = student_form.save()
            student.set_password(student.password)
            student.is_active = False
            my_group = Group.objects.get_or_create(name='Student')
            my_group[0].user_set.add(student)
            student.save()

            uidb64 = urlsafe_base64_encode(force_bytes(student.pk))
            domain = get_current_site(request).domain
            link = reverse('activate',kwargs={'uidb64':uidb64,'token':account_activation_token.make_token(student)})
            activate_url = 'http://' + domain +link
            email_subject = 'Activate your Exam Portal account'
            email_body = 'Hi.Please use this link to verify your account\n' + activate_url + ".\n\n You are receiving this message because you registered on " + domain +". If you didn't register please contact support team on " + domain 
            fromEmail = settings.DEFAULT_FROM_EMAIL
            email = EmailMessage(
				email_subject,
				email_body,
				fromEmail,
				[email],
            )
            student_info = student_info_form.save(commit=False)
            student_info.user = student
            if 'picture' in request.FILES:
                student_info.picture = request.FILES['picture']
            student_info.save()
            messages.success(request,"Registered Succesfully. Check Email for confirmation")
            EmailThread(email).start()
            return redirect('login')
        else:
            print(student_form.errors,student_info_form.errors)
            return render(request,'student/register.html',{'student_form':student_form,'student_info_form':student_info_form})
    
class LoginView(View):
	def get(self,request):
		return render(request,'student/login.html')
	
	def post(self,request):
		username = request.POST['username']
		password = request.POST['password']

		if username and password:
			try:
				user_ch = User.objects.get(username=username)
				if user_ch.is_staff:
					messages.error(request,"You are trying to login as student, but you have registered as faculty. We are redirecting you to faculty login. If you are having problem in logging in please reset password or contact admin")
					return redirect('faculty-login')
			except User.DoesNotExist:
				pass

			user = auth.authenticate(username=username,password=password)
			if user:
				if user.is_active:
					# NEW 2FA FLOW: Instead of directly logging in,
					# redirect to OTP verification page
					from core.two_factor_auth import TwoFactorAuth
					from django.http import QueryDict
					
					# Verify user has an email configured
					if not user.email:
						messages.error(request, "Your account does not have an email address configured. Please contact administrator to update your profile email.")
						return render(request, 'student/login.html')
					
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
						return render(request, 'student/login.html')
					
					# Send OTP email
					email_result = TwoFactorAuth.send_email_otp(
						session_id=session_result['session_id'],
						user_email=user.email,
						user_name=user.get_full_name() or user.username,
					)
					
					if not email_result['success']:
						messages.error(request, "Failed to send OTP. Please try again.")
						return render(request, 'student/login.html')
					
					# Redirect to OTP verification page
					import urllib.parse
					otp_url = f"/auth/otp/?session_id={session_result['session_id']}&email={urllib.parse.quote(user.email)}"
					return redirect(otp_url)
				else:
					messages.error(request,"Account is not active")
					return render(request,'student/login.html')
			else:
				messages.error(request,"Invalid Credentials")
				return render(request,'student/login.html')
		return render(request,'student/login.html')
	
	@staticmethod
	def get_client_ip(request):
		"""Extract client IP address from request."""
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			return x_forwarded_for.split(',')[0].strip()
		return request.META.get('REMOTE_ADDR', 'Unknown')

class LogoutView(View):
    def get(self, request):
        auth.logout(request)
        messages.success(request, 'Logged Out')
        return redirect('login')

    def post(self,request):
        auth.logout(request)
        messages.success(request,'Logged Out')
        return redirect('login')

class EmailThread(threading.Thread):
	def __init__(self,email):
		self.email = email
		threading.Thread.__init__(self)

	
	def run(self):
		self.email.send(fail_silently = False)

class VerificationView(View):
	def get(self,request,uidb64,token):
		try:
			id = force_str(urlsafe_base64_decode(uidb64))
			user = User.objects.get(pk=id)
			if not account_activation_token.check_token(user,token):
				messages.error(request,"User already Activated. Please Proceed With Login")
				return redirect("login")
			if user.is_active:
				return redirect('login')
			user.is_active = True
			user.save()
			messages.success(request,'Account activated Sucessfully')
			return redirect('login')
		except Exception as e:
			raise e
		return redirect('login')
