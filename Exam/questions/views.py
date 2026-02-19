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
        # list existing question papers for this professor
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
        if StuExam_DB.objects.filter(examname=exam.name ,student=request.user).exists():
            if StuExam_DB.objects.get(examname=exam.name,student=request.user).completed == 1:
                list_of_completed.append(exam)
        else:
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
    exams = Exam_Model.objects.all()
    list_of_completed = []
    list_un = []
    for exam in exams:
        if StuExam_DB.objects.filter(examname=exam.name ,student=request.user).exists():
            if StuExam_DB.objects.get(examname=exam.name,student=request.user).completed == 1:
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
    if request.method == 'GET':
        exam = Exam_Model.objects.get(pk=id)
        time_delta = exam.end_time - exam.start_time
        time = convert(time_delta.seconds)
        time = time.split(":")
        mins = time[0]
        secs = time[1]
        context = {
            "exam":exam,
            "question_list":exam.question_paper.questions.all(),
            "secs":secs,
            "mins":mins
        }
        return render(request,'exam/giveExam.html',context)
    if request.method == 'POST' :
        student = User.objects.get(username=request.user.username)
        paper = request.POST['paper']
        examMain = Exam_Model.objects.get(name = paper)
        stuExam = StuExam_DB.objects.get_or_create(examname=paper, student=student,qpaper = examMain.question_paper)[0]
        
        qPaper = examMain.question_paper
        stuExam.qpaper = qPaper
         
        qPaperQuestionsList = examMain.question_paper.questions.all()
        for ques in qPaperQuestionsList:
            student_question = Stu_Question(student=student,question=ques.question, optionA=ques.optionA, optionB=ques.optionB,optionC=ques.optionC, optionD=ques.optionD,
            answer=ques.answer)
            student_question.save()
            stuExam.questions.add(student_question)
            stuExam.save()

        stuExam.completed = 1
        stuExam.save()
        examQuestionsList = StuExam_DB.objects.filter(student=request.user,examname=paper,qpaper=examMain.question_paper,questions__student = request.user)[0]
        #examQuestionsList = stuExam.questions.all()
        examScore = 0
        list_i = examMain.question_paper.questions.all()
        queslist = examQuestionsList.questions.all()
        i = 0
        for j in range(list_i.count()):
            ques = queslist[j]
            max_m = list_i[i].max_marks
            ans = request.POST.get(ques.question, False)
            if not ans:
                ans = "E"
            ques.choice = ans
            ques.save()
            if ans.lower() == ques.answer.lower() or ans == ques.answer:
                examScore = examScore + max_m
            i+=1

        stuExam.score = examScore
        stuExam.save()
        stu = StuExam_DB.objects.filter(student=request.user,examname=examMain.name)  
        results = StuResults_DB.objects.get_or_create(student=request.user)[0]
        results.exams.add(stu[0])
        results.save()
        return redirect('view_exams_student')

@login_required(login_url='login')
def result(request,id):
    student = request.user
    exam = Exam_Model.objects.get(pk=id)
    score = StuExam_DB.objects.get(student=student,examname=exam.name,qpaper=exam.question_paper).score
    # Calculate SVG dashoffset for circular progress (stroke-dasharray = 440)
    max_dash = 440
    try:
        total = float(exam.total_marks) if exam.total_marks else 0.0
        ratio = float(score) / total if total > 0 else 0.0
    except Exception:
        ratio = 0.0
    if ratio < 0:
        ratio = 0.0
    if ratio > 1:
        ratio = 1.0
    dashoffset = int(max_dash * (1 - ratio))

    return render(request,'exam/result.html',{'exam':exam, "score":score, 'dashoffset': dashoffset})


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

    # render the dynamic question paper creation UI
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
    # create Question_DB objects and attach to Question_Paper; validate marks sum
    created_questions = []
    marks_sum = 0
    for q in questions:
        qtext = (q.get('question') or '').strip()
        optA = (q.get('optionA') or '').strip()
        optB = (q.get('optionB') or '').strip()
        optC = (q.get('optionC') or '').strip()
        optD = (q.get('optionD') or '').strip()
        answer = (q.get('answer') or '').strip()  # expect 'A'|'B'|'C'|'D'
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

    # validate marks sum equals total_marks
    if marks_sum != total_marks:
        # cleanup created questions
        for qq in created_questions:
            qq.delete()
        return JsonResponse({'success': False, 'error': 'Sum of question marks must equal total marks'}, status=400)

    qp = Question_Paper.objects.create(professor=prof, qPaperTitle=title, total_marks=total_marks)
    qp.questions.set(created_questions)
    qp.save()

    # return success with redirect target (create exam page)
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
