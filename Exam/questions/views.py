from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from .models import *
from django.contrib.auth.models import Group
from student.models import *
from django.utils import timezone
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
def view_exams_prof(request):
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
                return redirect('view_exams')

        exams = Exam_Model.objects.filter(professor=prof)
        return render(request, 'exam/mainexam.html', {
            'exams': exams, 'examform': new_Form, 'prof': prof,
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
    exams = Exam_Model.objects.filter(professor=prof)
    return render(request, 'exam/previousexam.html', {
        'exams': exams,'prof': prof
    })

@login_required(login_url='login')
def student_view_previous(request):
    exams = Exam_Model.objects.all()
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
    examn = Exam_Model.objects.filter(professor=request.user)
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
    students = User.objects.filter(groups__name = "Student")
    dicts = {}
    prof = request.user
    professor = User.objects.get(username=prof.username)
    examn = Exam_Model.objects.filter(professor=professor)
    for exam in examn:
        if StuExam_DB.objects.filter(examname=exam.name,completed=1).exists():
            students_filter = StuExam_DB.objects.filter(examname=exam.name,completed=1)
            for student in students_filter:
                key = str(student.student) + " " + str(student.examname) + " " + str(student.qpaper.qPaperTitle)
                dicts[key] = student.score
    return render(request, 'exam/resultsstudent.html', {
        'students':dicts
    })

@login_required(login_url='login')
def view_exams_student(request):
    # Get ALL exams - students should see all exams created by faculty
    exams = Exam_Model.objects.all().order_by('start_time')
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
            list_un.append(exam)

    return render(request,'exam/mainexamstudent.html',{
        'exams':list_un,
        'completed':list_of_completed
    })

@login_required(login_url='login')
def view_students_attendance(request):
    exams = Exam_Model.objects.all()
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
    
    if request.method == 'GET':
        time_delta = exam.end_time - exam.start_time
        time = convert(time_delta.seconds)
        time = time.split(":")
        mins = time[0]
        secs = time[1]
        
        existing_exam = StuExam_DB.objects.filter(student=student, examname=exam.name, completed=0).first()
        
        if existing_exam:
            pass
        
        context = {
            "exam":exam,
            "question_list":exam.question_paper.questions.all(),
            "secs":secs,
            "mins":mins,
            "hide_sidebar": True
        }
        return render(request,'exam/giveExam.html',context)
    
    if request.method == 'POST' :
        student = User.objects.get(username=request.user.username)
        examMain = Exam_Model.objects.get(pk=id)
        
        stuExam = StuExam_DB.objects.filter(
            examname=examMain.name, 
            student=student, 
            qpaper=examMain.question_paper,
            completed=0
        ).first()
        
        if not stuExam:
            stuExam = StuExam_DB.objects.get_or_create(
                examname=examMain.name, 
                student=student, 
                qpaper=examMain.question_paper,
                completed=0
            )[0]
        
        qPaper = examMain.question_paper
        stuExam.qpaper = qPaper
        
        qPaperQuestionsList = list(examMain.question_paper.questions.all())
        
        for ques in qPaperQuestionsList:
            student_question = Stu_Question(
                student=student,
                question=ques.question, 
                optionA=ques.optionA, 
                optionB=ques.optionB,
                optionC=ques.optionC, 
                optionD=ques.optionD,
                answer=ques.answer
            )
            student_question.save()
            stuExam.questions.add(student_question)
        
        stuExam.completed = 1
        stuExam.save()
        
        # Calculate exam score - iterate over POST data directly
        examScore = 0
        
        # Create a mapping of question text to question details for easy lookup
        # Store both original and stripped versions for robust matching
        question_map = {}
        for q in qPaperQuestionsList:
            # Store original question text
            question_map[q.question] = {
                'max_marks': q.max_marks,
                'answer': q.answer.upper() if q.answer else ''
            }
            # Also store stripped version
            question_map[q.question.strip()] = {
                'max_marks': q.max_marks,
                'answer': q.answer.upper() if q.answer else ''
            }
        
        # Iterate over POST data to find answers
        for key, value in request.POST.items():
            # Skip non-question fields
            if key.lower() in ['csrfmiddlewaretoken', 'paper', '']:
                continue
            
            # Get selected answer - convert to uppercase for comparison
            if not value:
                continue
            selected_answer = value.upper()
            
            # Look up the question in our map (try both original and stripped)
            q_info = None
            if key in question_map:
                q_info = question_map[key]
            elif key.strip() in question_map:
                q_info = question_map[key.strip()]
            
            if q_info:
                max_m = q_info['max_marks']
                correct_ans = q_info['answer']
                
                # Compare answers (both already uppercase)
                if selected_answer == correct_ans:
                    examScore += max_m
                
                # Update the student question choice
                stu_q = stuExam.questions.filter(question=key).first()
                if not stu_q:
                    stu_q = stuExam.questions.filter(question=key.strip()).first()
                if stu_q:
                    stu_q.choice = selected_answer
                    stu_q.save()

        # Update the score
        stuExam.score = examScore
        stuExam.save()
        
        # Save to results
        stu = StuExam_DB.objects.filter(
            student=request.user, 
            examname=examMain.name,
            qpaper=examMain.question_paper,
            completed=1
        ).first()
        
        if stu:
            results = StuResults_DB.objects.get_or_create(student=request.user)[0]
            results.exams.add(stu)
            results.save()
        
        # Redirect to result page to show the score
        return redirect('result', id=examMain.id)

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
        exam.delete()
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
