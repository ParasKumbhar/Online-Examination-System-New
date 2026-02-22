from django.urls import path
from . import views
urlpatterns = [
    path('prof/create-exam/',views.create_exam,name="create_exam"),
    path('prof/viewexams/',views.view_exams_prof,name="view_exams"),
    path('prof/viewpreviousexams/',views.view_previousexams_prof,name="faculty-previous"),
    path('prof/viewresults/',views.view_results_prof,name="faculty-result"),
    path('prof/addquestions/',views.add_questions,name="faculty-addquestions"),
    path('prof/addnewquestionpaper/',views.add_question_paper,name="faculty-add_question_paper"),
    path('prof/create-question-paper/', views.create_question_paper, name='faculty-create-question-paper'),
    path('prof/save-question-paper/', views.save_question_paper_ajax, name='faculty-save-question-paper'),
    path('prof/questionpaper/delete/<int:id>/', views.delete_question_paper, name='faculty-delete_qpaper'),
    path('prof/exam/edit/<int:id>/', views.edit_exam, name='faculty-edit_exam'),
    path('prof/exam/delete/<int:id>/', views.delete_exam, name='faculty-delete_exam'),
    path('prof/viewstudents/',views.view_students_prof,name="faculty-student"),
    
    # New enhanced exam edit URLs
    path('prof/exam/edit-enhanced/<int:id>/', views.edit_exam_enhanced, name='faculty-edit_exam_enhanced'),
    path('prof/api/questionpaper/<int:id>/', views.get_question_paper_api, name='faculty-get_qpaper_api'),
    path('prof/questionpaper/edit-from-exam/<int:id>/', views.edit_question_paper_from_exam, name='faculty-edit_qpaper_from_exam'),
    path('prof/update-question-paper/', views.update_question_paper_ajax, name='faculty-update-question-paper'),
    
    path('student/viewexams/',views.view_exams_student,name="view_exams_student"),
    path('student/previous/',views.student_view_previous,name="student-previous"),
    path('student/appear/<int:id>',views.appear_exam,name = "appear-exam"),
    path('student/result/<int:id>',views.result,name = "result"),
    path('student/attendance/',views.view_students_attendance,name="view_students_attendance")
]