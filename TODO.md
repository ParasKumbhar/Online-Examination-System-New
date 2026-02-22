# TODO: Remove Total Marks from Exam Forms

## Task
Remove total marks input from Exam create/edit forms, but keep it in Question Paper create/edit forms.

## Steps
- [x] 1. Update ExamForm in models.py - exclude total_marks from form
- [x] 2. Update edit_exam_enhanced.html - remove total_marks field
- [x] 3. Update mainexam.html - form will auto-exclude total_marks (via form)
- [x] 4. Update editsingleexam.html - form will auto-exclude total_marks (via form)
- [x] 5. Update previousexam.html - show total_marks from question_paper
- [x] 6. Update views.py - use question_paper.total_marks where needed
- [x] 7. Update notifications/models.py - use question_paper.total_marks
- [x] 8. Update api/views.py - use question_paper.total_marks
- [x] 9. Update api/serializers.py - use SerializerMethodField for total_marks

## Summary
Removed total marks input from Exam create/edit forms. The total marks now comes from the Question Paper instead. The Question Paper creation/edit still has the total marks input as requested.
