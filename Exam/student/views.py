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
    from django.utils import timezone
    from django.db.models import Avg, Sum
    
    student = request.user
    
    # Get ALL exams - students should see all exams created by faculty
    all_exams = Exam_Model.objects.all().order_by('start_time')
    
    # Filter out exams that the student has already completed
    upcoming_exams = []
    for exam in all_exams:
        is_completed = StuExam_DB.objects.filter(
            student=student,
            examname=exam.name,
            qpaper=exam.question_paper,
            completed=1
        ).exists()
        
        if not is_completed:
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
        'rank': rank
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
		return render(request,'student\login.html')
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
					auth.login(request,user)
					email = user.email

					email_subject = 'You Logged into your Portal account'
					email_body = "If you think someone else logged in. Please contact support or reset your password.\n\nYou are receving this message because you have enabled login email notifications in portal settings. If you don't want to recieve such emails in future please turn the login email notifications off in settings."
					fromEmail = settings.DEFAULT_FROM_EMAIL
					email_msg = EmailMessage(
						email_subject,
						email_body,
						fromEmail,
						[email],
					)
					
					student_pref = StudentPreferenceModel.objects.filter(user=user).first()
					if student_pref and not student_pref.sendEmailOnLogin:
						pass
					else:
						EmailThread(email_msg).start()

					return redirect('index')
				else:
					messages.error(request,"Account is not active")
					return render(request,'student\login.html')
			else:
				messages.error(request,"Invalid Credentials")
				return render(request,'student\login.html')
		return render(request,'student\login.html')

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
