from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from .models import *
from django.contrib.auth.models import Group
from student.models import *
from django.utils import timezone
import random
from django.core.mail import send_mail
from django.conf import settings
from student.models import StuExam_DB,StuResults_DB
from questions.questionpaper_models import QPForm
from questions.question_models import QForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from .models import Exam_Model, ExamForm
from django.http import JsonResponse, HttpResponseBadRequest
import json

def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@login_required(login_url='faculty-login')
def create_exam(request):
    """View for creating a new exam - separate page with only creation form"""
    prof = request.user
    permissions = False
    if prof:
        permissions = has_group(prof,"Professor")
    if permissions:
        new_Form = ExamForm(prof)
        if request.method == 'POST' and permissions:
            form = ExamForm(prof,request.POST)
            if form.is_valid():
                exam = form.save(commit=False)
                exam.professor = prof
                exam.save()
                form.save_m2m()
                from django.contrib import messages
                messages.success(request, 'Exam created successfully!')
                return redirect('create_exam')

        return render(request, 'exam/create_exam.html', {
            'examform': new_Form, 'prof': prof,
        })
    else:
        return redirect('view_exams_student')

@login_required(login_url='faculty-login')
def view_exams_prof(request):
    """View for managing exams - shows list of exams only"""
    prof = request.user
    permissions = False
    if prof:
        permissions = has_group(prof,"Professor")
    if permissions:
        exams = Exam_Model.objects.filter(professor=prof, is_active=True)
        return render(request, 'exam/mainexam.html', {
            'exams': exams, 'prof': prof,
        })
    else:
        return redirect('view_exams_student')

@login_required(login_url='faculty-login')
def add_question_paper(request):
    prof = request.user
    permissions = False
    if prof:
        permissions = has_group(prof,"Professor")
    if permissions:
        new_Form = QPForm(prof)
        if request.method == 'POST' and permissions:
            form = QPForm(prof,request.POST)
            if form.is_valid():
                exam = form.save(commit=False)
                exam.professor = prof
                exam.save()
                form.save_m2m()
                return redirect('faculty-add_question_paper')

        exams = Exam_Model.objects.filter(professor=prof)
        qpapers = Question_Paper.objects.filter(professor=prof)
        return render(request, 'exam/addquestionpaper.html', {
            'exams': exams, 'examform': new_Form, 'prof': prof, 'qpapers': qpapers,
        })
    else:
        return redirect('view_exams_student')

@login_required(login_url='faculty-login')
def add_questions(request):
    prof = request.user
    permissions = False
    if prof:
        permissions = has_group(prof,"Professor")
    if permissions:
        new_Form = QForm()
        if request.method == 'POST' and permissions:
            form = QForm(request.POST)
            if form.is_valid():
                exam = form.save(commit=False)
                exam.professor = prof
                exam.save()
                form.save_m2m()
                return redirect('faculty-addquestions')

        exams = Exam_Model.objects.filter(professor=prof)
        return render(request, 'exam/addquestions.html', {
            'exams': exams, 'examform': new_Form, 'prof': prof,
        })
    else:
        return redirect('view_exams_student')

@login_required(login_url='faculty-login')
def view_previousexams_prof(request):
    prof = request.user
    student = 0
    exams = Exam_Model.objects.filter(professor=prof, is_active=True)
    return render(request, 'exam/previousexam.html', {
        'exams': exams,'prof': prof
    })

@login_required(login_url='login')
def student_view_previous(request):
    exams = Exam_Model.objects.filter(is_active=True)
    list_of_completed = []
    list_un = []
    for exam in exams:
        stu_exam = StuExam_DB.objects.filter(
            examname=exam.name,
            student=request.user,
            qpaper=exam.question_paper,
            completed=1
        ).first()
        
        if stu_exam:
            list_of_completed.append(exam)
        else:
            any_record = StuExam_DB.objects.filter(
                examname=exam.name,
                student=request.user,
                qpaper=exam.question_paper
            ).exists()
            
            if not any_record:
                list_un.append(exam)

    return render(request,'exam/previousstudent.html',{
        'exams':list_un,
        'completed':list_of_completed
    })

@login_required(login_url='faculty-login')
def view_students_prof(request):
    students = User.objects.filter(groups__name = "Student")
    student_name = []
    student_completed = []
    count = 0
    dicts = {}
    examn = Exam_Model.objects.filter(professor=request.user, is_active=True)
    for student in students:
        student_name.append(student.username)
        count = 0
        for exam in examn:
            if StuExam_DB.objects.filter(student=student,examname=exam.name,completed=1).exists():
                count += 1
            else:
                count += 0
        student_completed.append(count)
    i = 0
    for x in student_name:
        dicts[x] = student_completed[i]
        i+=1
    return render(request, 'exam/viewstudents.html', {
        'students':dicts
    })

@login_required(login_url='faculty-login')
def view_results_prof(request):
    """
    View for faculty to see all student results organized by student.
    Each student shows their results for all exams created by this professor.
    """
    prof = request.user
    
    # Get all active exams created by this professor
    professor_exams = Exam_Model.objects.filter(professor=prof, is_active=True)
    
    # Get all students who took any of professor's exams
    student_results = {}
    
    for exam in professor_exams:
        # Get all completed exam attempts for this exam
        exam_attempts = StuExam_DB.objects.filter(
            examname=exam.name,
            qpaper=exam.question_paper,
            completed=1
        ).select_related('student', 'qpaper')
        
        for attempt in exam_attempts:
            student_username = str(attempt.student.username)
            
            # Get student's full name if available
            student_first_name = attempt.student.first_name
            student_last_name = attempt.student.last_name
            if student_first_name or student_last_name:
                student_display_name = f"{student_first_name} {student_last_name}".strip()
            else:
                student_display_name = student_username
            
            # Calculate total marks for this exam
            total_marks = 0
            if attempt.qpaper:
                for question in attempt.qpaper.questions.all():
                    total_marks += question.max_marks
            
            # Calculate percentage
            percentage = 0
            if total_marks > 0:
                percentage = round((attempt.score / total_marks) * 100, 1)
            
            # Create exam result data
            exam_result = {
                'exam_name': exam.name,
                'question_paper': attempt.qpaper.qPaperTitle if attempt.qpaper else 'N/A',
                'score': attempt.score,
                'total_marks': total_marks,
                'percentage': percentage,
                'attempt_id': attempt.id,
                'exam_date': exam.start_time,
            }
            
            # Add to student results dictionary
            if student_username not in student_results:
                student_results[student_username] = {
                    'display_name': student_display_name,
                    'exams': []
                }
            
            student_results[student_username]['exams'].append(exam_result)
    
    # Sort students by name
    sorted_students = dict(sorted(student_results.items()))
    
    return render(request, 'exam/resultsstudent.html', {
        'student_results': sorted_students
    })

@login_required(login_url='login')
def view_exams_student(request):
    # Get ALL active exams - students should see all active exams created by faculty
    exams = Exam_Model.objects.filter(is_active=True).order_by('start_time')
    list_of_completed = []
    list_un = []
    now = timezone.localtime()

    # Ensure stored times are timezone-aware and localised
    def _ensure_aware(dt):
        if not dt:
            return dt
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_default_timezone())
        return timezone.localtime(dt)

    for exam in exams:
        exam.start_time = _ensure_aware(exam.start_time)
        exam.end_time = _ensure_aware(exam.end_time)
        stu_exam = StuExam_DB.objects.filter(
            examname=exam.name,
            student=request.user,
            qpaper=exam.question_paper
        ).first()

        # If the exam window has passed, automatically mark as completed with zero score if not already
        if exam.end_time and now > exam.end_time:
            if not stu_exam:
                stu_exam = StuExam_DB.objects.create(
                    student=request.user,
                    examname=exam.name,
                    qpaper=exam.question_paper,
                    score=0,
                    completed=1
                )
            else:
                stu_exam.completed = 1
                stu_exam.score = stu_exam.score or 0
                stu_exam.save()

            # Add to results tracking if not already
            results = StuResults_DB.objects.get_or_create(student=request.user)[0]
            if stu_exam not in results.exams.all():
                results.exams.add(stu_exam)

            list_of_completed.append(exam)
            continue

        # Check if student has already completed this exam FIRST
        if stu_exam and stu_exam.completed == 1:
            list_of_completed.append(exam)
            continue

        # Allow students to start the exam only during the scheduled window
        exam.can_appear = False
        if exam.start_time and now >= exam.start_time:
            if not exam.end_time or now <= exam.end_time:
                exam.can_appear = True

        # Only add to available exams if student can appear and hasn't completed
        if exam.can_appear:
            list_un.append(exam)
        else:
            # Exam is either not started yet or has ended - add to completed
            list_of_completed.append(exam)

    return render(request,'exam/mainexamstudent.html',{
        'exams':list_un,
        'completed':list_of_completed,
        'now': now,
    })

@login_required(login_url='login')
def view_students_attendance(request):
    exams = Exam_Model.objects.filter(is_active=True)
    list_of_completed = []
    list_un = []
    for exam in exams:
        if StuExam_DB.objects.filter(examname=exam.name ,student=request.user).exists():
            if StuExam_DB.objects.get(examname=exam.name,student=request.user).completed == 1:
                list_of_completed.append(exam)
        else:
            list_un.append(exam)

    return render(request,'exam/attendance.html',{
        'exams':list_un,
        'completed':list_of_completed
    })

def convert(seconds): 
    min, sec = divmod(seconds, 60) 
    hour, min = divmod(min, 60) 
    min += hour*60
    return "%02d:%02d" % (min, sec) 

@login_required(login_url='login')
def appear_exam(request,id):
    student = request.user
    
    # Get the exam first
    exam = Exam_Model.objects.get(pk=id)
    now = timezone.localtime()

    # Ensure stored times are timezone-aware and localised
    def _ensure_aware(dt):
        if not dt:
            return dt
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_default_timezone())
        return timezone.localtime(dt)

    exam.start_time = _ensure_aware(exam.start_time)
    exam.end_time = _ensure_aware(exam.end_time)

    # Prevent access outside the scheduled window
    if exam.start_time and now < exam.start_time:
        start_local = timezone.localtime(exam.start_time).strftime("%b %d, %Y at %H:%M")
        from django.contrib import messages
        messages.error(request, f"The exam is accessible starting on {start_local}. Please return then.")
        return redirect('view_exams_student')

    if exam.end_time and now > exam.end_time:
        # Auto-mark student as absent (0 score) when past end time
        stu_exam = StuExam_DB.objects.filter(
            student=student,
            examname=exam.name,
            qpaper=exam.question_paper
        ).first()
        if not stu_exam:
            stu_exam = StuExam_DB.objects.create(
                student=student,
                examname=exam.name,
                qpaper=exam.question_paper,
                score=0,
                completed=1
            )
        else:
            stu_exam.completed = 1
            stu_exam.score = stu_exam.score or 0
            stu_exam.save()

        results = StuResults_DB.objects.get_or_create(student=student)[0]
        if stu_exam not in results.exams.all():
            results.exams.add(stu_exam)

        from django.contrib import messages
        messages.error(request, "The exam time has ended. You have been marked absent with a score of 0.")
        return redirect('result', id=exam.id)

    # Check if student has already completed this exam - prevent retake
    existing_completed = StuExam_DB.objects.filter(
        student=student,
        examname=exam.name,
        qpaper=exam.question_paper,
        completed=1
    ).first()

    if existing_completed:
        from django.contrib import messages
        messages.error(request, "You have already completed this exam. You cannot retake it.")
        return redirect('view_exams_student')
    
    # Create or retrieve the exam session with randomized question/order state
    def _get_client_ip(req):
        x_forwarded_for = req.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return req.META.get('REMOTE_ADDR', '0.0.0.0')

    from questions.anticheating_models import ExamSession, ExamSecurityAlert
    from questions.question_models import Question_DB

    exam_session, created_session = ExamSession.objects.get_or_create(
        student=student,
        exam=exam,
        defaults={
            'duration_seconds': int((exam.end_time - exam.start_time).total_seconds()),
            'ends_at': exam.end_time,
            'ip_address': _get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )

    if created_session or not exam_session.question_order:
        all_questions = list(exam.question_paper.questions.all())
        question_order = [q.qno for q in all_questions]
        random.shuffle(question_order)

        option_order = {}
        for q in all_questions:
            opts = ['A', 'B', 'C', 'D']
            random.shuffle(opts)
            option_order[str(q.qno)] = opts

        exam_session.question_order = question_order
        exam_session.option_order = option_order
        exam_session.ends_at = exam.end_time
        exam_session.save()

    # Evaluate remaining time as seconds from now
    remaining_timedelta = max(0, int((exam.end_time - now).total_seconds()))
    mins = remaining_timedelta // 60
    secs = remaining_timedelta % 60

    if request.method == 'GET':
        ordered_questions = []
        for qno in exam_session.question_order:
            q = Question_DB.objects.get(qno=qno)
            mapped_options = []
            for letter in exam_session.option_order.get(str(qno), ['A', 'B', 'C', 'D']):
                mapped_options.append({'choice': letter, 'text': getattr(q, 'option' + letter)})

            ordered_questions.append({
                'qno': q.qno,
                'question': q.question,
                'max_marks': q.max_marks,
                'options': mapped_options
            })

        context = {
            'exam': exam,
            'question_list': ordered_questions,
            'secs': secs,
            'mins': mins,
            'exam_session_id': exam_session.id,
            'hide_sidebar': True
        }
        return render(request, 'exam/giveExam.html', context)

    if request.method == 'POST':
        # Prevent retake and timeout
        if now > exam.end_time:
            from django.contrib import messages
            messages.error(request, 'Time expired; exam has been auto-submitted.')
            # Mark session as submitted, no score update
            exam_session.mark_submitted()
            return redirect('result', id=exam.id)

        if exam_session.is_submitted:
            from django.contrib import messages
            messages.error(request, 'This exam session has already been submitted.')
            return redirect('view_exams_student')

        already_completed = StuExam_DB.objects.filter(
            examname=exam.name,
            student=student,
            qpaper=exam.question_paper,
            completed=1
        ).exists()

        if already_completed:
            from django.contrib import messages
            messages.error(request, 'You have already completed this exam. You cannot retake it.')
            return redirect('view_exams_student')

        # Create or continue existing StuExam_DB row
        stuExam, _ = StuExam_DB.objects.get_or_create(
            examname=exam.name,
            student=student,
            qpaper=exam.question_paper,
            defaults={'completed': 0, 'score': 0}
        )

        stuExam.qpaper = exam.question_paper

        # Persist student question snapshots in result table (optional)
        for qno in exam_session.question_order:
            try:
                qrec = Question_DB.objects.get(qno=qno)
            except Question_DB.DoesNotExist:
                continue

            student_question = Stu_Question.objects.create(
                student=student,
                question=qrec.question,
                optionA=qrec.optionA,
                optionB=qrec.optionB,
                optionC=qrec.optionC,
                optionD=qrec.optionD,
                answer=qrec.answer
            )
            stuExam.questions.add(student_question)

        # Score calculation from server-side data and form values
        examScore = 0
        for qno in exam_session.question_order:
            try:
                qrec = Question_DB.objects.get(qno=qno)
            except Question_DB.DoesNotExist:
                continue

            answer_key = 'answer_{}'.format(qno)
            selected = request.POST.get(answer_key, '').upper().strip()
            if selected and selected == qrec.answer.upper():
                examScore += qrec.max_marks

            stu_q = stuExam.questions.filter(question=qrec.question).last()
            if stu_q:
                stu_q.choice = selected
                stu_q.save()

        stuExam.score = examScore
        stuExam.completed = 1
        stuExam.save()

        # Mark exam session submitted
        exam_session.mark_submitted()

        # Add to results table
        results = StuResults_DB.objects.get_or_create(student=student)[0]
        results.exams.add(stuExam)

        # Flag if suspicious events exceeded
        if exam_session.tab_switch_count >= 5 or exam_session.fullscreen_exit_count >= 3:
            alert_reason = 'Tab switches: {}, fullscreen exits: {}'.format(
                exam_session.tab_switch_count, exam_session.fullscreen_exit_count
            )
            ExamSecurityAlert.objects.create(
                student=student,
                exam=exam,
                alert_type='AUTO_SUBMIT_SUSPICION',
                level='CRITICAL',
                message=alert_reason
            )

        return redirect('result', id=exam.id)

@login_required(login_url='login')
def result(request,id):
    student = request.user
    exam = get_object_or_404(Exam_Model, pk=id)
    
    stu_exam = StuExam_DB.objects.filter(
        student=student,
        examname=exam.name,
        qpaper=exam.question_paper
    ).first()
    
    if not stu_exam:
        stu_exam = StuExam_DB.objects.filter(
            student=student,
            examname=exam.name,
            completed=1
        ).first()
    
    if not stu_exam:
        from django.contrib import messages
        messages.error(request, "No exam record found. Please complete the exam first.")
        return redirect('view_exams_student')
    
    score = stu_exam.score
    
    total_marks = 0
    for q in exam.question_paper.questions.all():
        total_marks += q.max_marks
    
    max_dash = 440
    try:
        ratio = float(score) / total_marks if total_marks > 0 else 0.0
    except Exception:
        ratio = 0.0
    if ratio < 0:
        ratio = 0.0
    if ratio > 1:
        ratio = 1.0
    dashoffset = int(max_dash * (1 - ratio))

    return render(request,'exam/result.html',{'exam':exam, "score":score, 'total_marks': total_marks, 'dashoffset': dashoffset})


@login_required(login_url='faculty-login')
def edit_question_paper(request, id):
    prof = request.user
    qp = get_object_or_404(Question_Paper, pk=id)
    if qp.professor != prof:
        return HttpResponseForbidden("You don't have permission to edit this question paper.")

    if request.method == 'POST':
        form = QPForm(prof, request.POST, instance=qp)
        if form.is_valid():
            form.save()
            return redirect('faculty-add_question_paper')
    else:
        form = QPForm(prof, instance=qp)

    return render(request, 'exam/editquestionpaper.html', {'examform': form, 'qp': qp, 'prof': prof})


@login_required(login_url='faculty-login')
def create_question_paper(request):
    prof = request.user
    permissions = False
    if prof:
        permissions = has_group(prof,"Professor")
    if not permissions:
        return redirect('view_exams_student')

    return render(request, 'exam/create_question_paper.html', {'prof': prof, 'hide_sidebar': True})


@login_required(login_url='faculty-login')
def save_question_paper_ajax(request):
    if request.method != 'POST' or not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponseBadRequest('Invalid request')

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('Invalid JSON')

    title = payload.get('title', '').strip()
    try:
        total_marks = int(payload.get('total_marks') or 0)
    except Exception:
        total_marks = 0
    questions = payload.get('questions', [])
    if not title or total_marks <= 0 or not isinstance(questions, list) or len(questions) == 0:
        return JsonResponse({'success': False, 'error': 'Missing title, total marks, or questions'}, status=400)

    prof = request.user
    created_questions = []
    marks_sum = 0
    for q in questions:
        qtext = (q.get('question') or '').strip()
        optA = (q.get('optionA') or '').strip()
        optB = (q.get('optionB') or '').strip()
        optC = (q.get('optionC') or '').strip()
        optD = (q.get('optionD') or '').strip()
        answer = (q.get('answer') or '').strip()
        max_marks = q.get('max_marks') or 0
        if not qtext or not optA or not optB or not optC or not optD or answer not in ['A','B','C','D']:
            return JsonResponse({'success': False, 'error': 'Invalid question data'}, status=400)

        try:
            mm = int(max_marks)
        except Exception:
            mm = 0
        marks_sum += mm

        question_obj = Question_DB.objects.create(
            professor=prof,
            question=qtext,
            optionA=optA,
            optionB=optB,
            optionC=optC,
            optionD=optD,
            answer=answer,
            max_marks=mm
        )
        created_questions.append(question_obj)

    if marks_sum != total_marks:
        for qq in created_questions:
            qq.delete()
        return JsonResponse({'success': False, 'error': 'Sum of question marks must equal total marks'}, status=400)

    qp = Question_Paper.objects.create(professor=prof, qPaperTitle=title, total_marks=total_marks)
    qp.questions.set(created_questions)
    qp.save()

    return JsonResponse({'success': True, 'redirect': '/exams/prof/viewexams/'})


@login_required(login_url='faculty-login')
def delete_question_paper(request, id):
    prof = request.user
    qp = get_object_or_404(Question_Paper, pk=id)
    if qp.professor != prof:
        return HttpResponseForbidden("You don't have permission to delete this question paper.")

    if request.method == 'POST':
        qp.delete()
        return redirect('faculty-add_question_paper')

    return render(request, 'exam/delete_qpaper.html', {'qp': qp})


@login_required(login_url='faculty-login')
def edit_exam(request, id):
    prof = request.user
    exam = get_object_or_404(Exam_Model, pk=id)
    if exam.professor != prof:
        return HttpResponseForbidden("You don't have permission to edit this exam.")

    if request.method == 'POST':
        # Preserve original exam identifiers so we can reset student records if the schedule changes
        original_name = exam.name
        original_qpaper = exam.question_paper
        original_start = exam.start_time
        original_end = exam.end_time

        form = ExamForm(prof, request.POST, instance=exam)
        if form.is_valid():
            ex = form.save(commit=False)
            ex.professor = prof
            ex.save()
            form.save_m2m()

            return redirect('view_exams')
    else:
        form = ExamForm(prof, instance=exam)

    return render(request, 'exam/editsingleexam.html', {'examform': form, 'exam': exam})


@login_required(login_url='faculty-login')
def delete_exam(request, id):
    prof = request.user
    exam = get_object_or_404(Exam_Model, pk=id)
    if exam.professor != prof:
        return HttpResponseForbidden("You don't have permission to delete this exam.")

    if request.method == 'POST':
        from student.models import StuExam_DB
        StuExam_DB.objects.filter(examname=exam.name, qpaper=exam.question_paper).delete()
        exam.is_active = False
        exam.save()
        return redirect('view_exams')

    return render(request, 'exam/delete_exam.html', {'exam': exam})


@login_required(login_url='faculty-login')
def edit_exam_enhanced(request, id):
    """Enhanced exam edit with question paper editing capability"""
    from django.contrib import messages
    prof = request.user
    exam = get_object_or_404(Exam_Model, pk=id)
    if exam.professor != prof:
        return HttpResponseForbidden("You don't have permission to edit this exam.")

    if request.method == 'POST':
        # Preserve original exam identifiers so we can reset student records if the schedule changes
        original_name = exam.name
        original_qpaper = exam.question_paper
        original_start = exam.start_time
        original_end = exam.end_time

        form = ExamForm(prof, request.POST, instance=exam)
        if form.is_valid():
            ex = form.save(commit=False)
            ex.professor = prof
            ex.save()
            form.save_m2m()

            messages.success(request, 'Exam details updated successfully!')
            return redirect('faculty-edit_exam_enhanced', id=exam.id)
    else:
        form = ExamForm(prof, instance=exam)

    # Get question paper info
    qpaper = exam.question_paper
    question_count = qpaper.questions.count() if qpaper else 0

    return render(request, 'exam/edit_exam_enhanced.html', {
        'examform': form, 
        'exam': exam,
        'qpaper': qpaper,
        'question_count': question_count
    })


@login_required(login_url='faculty-login')
def get_question_paper_api(request, id):
    """API endpoint to get question paper data with all questions"""
    prof = request.user
    qpaper = get_object_or_404(Question_Paper, pk=id)
    
    if qpaper.professor != prof:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    questions = []
    for q in qpaper.questions.all():
        questions.append({
            'id': q.qno,
            'question': q.question,
            'optionA': q.optionA,
            'optionB': q.optionB,
            'optionC': q.optionC,
            'optionD': q.optionD,
            'answer': q.answer,
            'max_marks': q.max_marks
        })
    
    return JsonResponse({
        'id': qpaper.id,
        'title': qpaper.qPaperTitle,
        'total_marks': qpaper.total_marks,
        'questions': questions
    })


@login_required(login_url='faculty-login')
def edit_question_paper_from_exam(request, id):
    """Edit question paper from exam edit page - loads in the question paper editor"""
    prof = request.user
    qpaper = get_object_or_404(Question_Paper, pk=id)
    
    if qpaper.professor != prof:
        return HttpResponseForbidden("You don't have permission to edit this question paper.")
    
    # Get the exam that uses this question paper
    exam = Exam_Model.objects.filter(question_paper=qpaper).first()
    
    # Pass the exam ID to the template so we can redirect back after editing
    return render(request, 'exam/create_question_paper.html', {
        'prof': prof,
        'qpaper': qpaper,
        'exam_id': exam.id if exam else None,
        'edit_mode': True,
        'hide_sidebar': True
    })


@login_required(login_url='faculty-login')
def update_question_paper_ajax(request):
    """AJAX endpoint to update an existing question paper"""
    if request.method != 'POST' or not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    qpaper_id = payload.get('qpaper_id')
    if not qpaper_id:
        return JsonResponse({'error': 'Question paper ID required'}, status=400)
    
    prof = request.user
    try:
        qpaper = Question_Paper.objects.get(pk=qpaper_id, professor=prof)
    except Question_Paper.DoesNotExist:
        return JsonResponse({'error': 'Question paper not found'}, status=404)

    title = payload.get('title', '').strip()
    try:
        total_marks = int(payload.get('total_marks') or 0)
    except Exception:
        total_marks = 0
    questions = payload.get('questions', [])
    
    if not title or total_marks <= 0 or not isinstance(questions, list) or len(questions) == 0:
        return JsonResponse({'error': 'Missing title, total marks, or questions'}, status=400)

    # Update question paper
    qpaper.qPaperTitle = title
    qpaper.total_marks = total_marks
    
    # Clear existing questions
    qpaper.questions.clear()
    
    # Process questions
    created_questions = []
    marks_sum = 0
    for q in questions:
        qtext = (q.get('question') or '').strip()
        optA = (q.get('optionA') or '').strip()
        optB = (q.get('optionB') or '').strip()
        optC = (q.get('optionC') or '').strip()
        optD = (q.get('optionD') or '').strip()
        answer = (q.get('answer') or '').strip()
        max_marks = q.get('max_marks') or 0
        
        if not qtext or not optA or not optB or not optC or not optD or answer not in ['A','B','C','D']:
            return JsonResponse({'error': 'Invalid question data'}, status=400)

        try:
            mm = int(max_marks)
        except Exception:
            mm = 0
        marks_sum += mm

        question_obj = Question_DB.objects.create(
            professor=prof,
            question=qtext,
            optionA=optA,
            optionB=optB,
            optionC=optC,
            optionD=optD,
            answer=answer,
            max_marks=mm
        )
        created_questions.append(question_obj)

    if marks_sum != total_marks:
        for qq in created_questions:
            qq.delete()
        return JsonResponse({'error': 'Sum of question marks must equal total marks'}, status=400)

    # Add questions to question paper
    qpaper.questions.set(created_questions)
    qpaper.save()

    # Get the exam to redirect back
    exam = Exam_Model.objects.filter(question_paper=qpaper).first()
    
    return JsonResponse({
        'success': True, 
        'redirect': f'/exams/prof/exam/edit-enhanced/{exam.id}/' if exam else '/exams/prof/viewexams/'
    })
