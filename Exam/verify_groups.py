#!/usr/bin/env python
"""
Verify Groups and Permissions Setup
This script checks that all groups and permissions are correctly configured
"""

import os
import sys
import django
from collections import defaultdict

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examProject.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def verify_groups_and_permissions():
    print("=" * 80)
    print("GROUPS AND PERMISSIONS VERIFICATION REPORT")
    print("=" * 80)
    
    # Expected permissions for each group
    expected_professor_perms = {
        ('add_question_db', 'questions'),
        ('change_question_db', 'questions'),
        ('delete_question_db', 'questions'),
        ('view_question_db', 'questions'),
        ('add_question_paper', 'questions'),
        ('change_question_paper', 'questions'),
        ('delete_question_paper', 'questions'),
        ('view_question_paper', 'questions'),
        ('add_exam_model', 'questions'),
        ('change_exam_model', 'questions'),
        ('delete_exam_model', 'questions'),
        ('view_exam_model', 'questions'),
        ('add_questioncategory', 'questions'),
        ('change_questioncategory', 'questions'),
        ('delete_questioncategory', 'questions'),
        ('view_questioncategory', 'questions'),
        ('add_questiontag', 'questions'),
        ('change_questiontag', 'questions'),
        ('delete_questiontag', 'questions'),
        ('view_questiontag', 'questions'),
        ('add_questionversion', 'questions'),
        ('change_questionversion', 'questions'),
        ('delete_questionversion', 'questions'),
        ('view_questionversion', 'questions'),
        ('add_questionstatistics', 'questions'),
        ('change_questionstatistics', 'questions'),
        ('delete_questionstatistics', 'questions'),
        ('view_questionstatistics', 'questions'),
        ('add_examassignment', 'questions'),
        ('change_examassignment', 'questions'),
        ('delete_examassignment', 'questions'),
        ('view_examassignment', 'questions'),
        ('add_examfocuslog', 'questions'),
        ('change_examfocuslog', 'questions'),
        ('delete_examfocuslog', 'questions'),
        ('view_examfocuslog', 'questions'),
        ('add_examsecurityalert', 'questions'),
        ('change_examsecurityalert', 'questions'),
        ('delete_examsecurityalert', 'questions'),
        ('view_examsecurityalert', 'questions'),
        ('add_examsession', 'questions'),
        ('change_examsession', 'questions'),
        ('delete_examsession', 'questions'),
        ('view_examsession', 'questions'),
        ('add_focuslossevent', 'questions'),
        ('change_focuslossevent', 'questions'),
        ('delete_focuslossevent', 'questions'),
        ('view_focuslossevent', 'questions'),
        ('add_facultyinfo', 'faculty'),
        ('change_facultyinfo', 'faculty'),
        ('delete_facultyinfo', 'faculty'),
        ('view_facultyinfo', 'faculty'),
        ('add_course', 'course'),
        ('change_course', 'course'),
        ('delete_course', 'course'),
        ('view_course', 'course'),
        ('add_session', 'course'),
        ('change_session', 'course'),
        ('delete_session', 'course'),
        ('view_session', 'course'),
        ('add_courseregistration', 'course'),
        ('change_courseregistration', 'course'),
        ('delete_courseregistration', 'course'),
        ('view_courseregistration', 'course'),
        ('add_grade', 'course'),
        ('change_grade', 'course'),
        ('delete_grade', 'course'),
        ('view_grade', 'course'),
        ('add_studentacceptance', 'course'),
        ('change_studentacceptance', 'course'),
        ('delete_studentacceptance', 'course'),
        ('view_studentacceptance', 'course'),
        ('add_configmarks', 'resultprocessing'),
        ('change_configmarks', 'resultprocessing'),
        ('delete_configmarks', 'resultprocessing'),
        ('view_configmarks', 'resultprocessing'),
        ('view_score', 'resultprocessing'),
        ('view_student', 'resultprocessing'),
        ('view_program', 'resultprocessing'),
        ('view_notification', 'notifications'),
        ('view_notificationpreference', 'notifications'),
    }
    
    expected_student_perms = {
        ('add_studentinfo', 'student'),
        ('change_studentinfo', 'student'),
        ('delete_studentinfo', 'student'),
        ('view_studentinfo', 'student'),
        ('add_stu_question', 'student'),
        ('change_stu_question', 'student'),
        ('delete_stu_question', 'student'),
        ('view_stu_question', 'student'),
        ('add_stuexam_db', 'student'),
        ('change_stuexam_db', 'student'),
        ('delete_stuexam_db', 'student'),
        ('view_stuexam_db', 'student'),
        ('add_sturesults_db', 'student'),
        ('change_sturesults_db', 'student'),
        ('delete_sturesults_db', 'student'),
        ('view_sturesults_db', 'student'),
        ('view_question_db', 'questions'),
        ('view_question_paper', 'questions'),
        ('view_exam_model', 'questions'),
        ('view_questioncategory', 'questions'),
        ('view_questiontag', 'questions'),
        ('view_questionversion', 'questions'),
        ('view_questionstatistics', 'questions'),
        ('view_examassignment', 'questions'),
        ('view_examsession', 'questions'),
        ('view_focuslossevent', 'questions'),
        ('view_courseregistration', 'course'),
        ('view_grade', 'course'),
        ('view_studentacceptance', 'course'),
        ('view_score', 'resultprocessing'),
        ('add_studentpreferencemodel', 'studentPreferences'),
        ('change_studentpreferencemodel', 'studentPreferences'),
        ('delete_studentpreferencemodel', 'studentPreferences'),
        ('view_studentpreferencemodel', 'studentPreferences'),
        ('add_notificationpreference', 'notifications'),
        ('change_notificationpreference', 'notifications'),
        ('view_notificationpreference', 'notifications'),
        ('view_notification', 'notifications'),
        ('add_studentwallet', 'tuition'),
        ('change_studentwallet', 'tuition'),
        ('view_studentwallet', 'tuition'),
        ('view_librarybook', 'tuition'),
        ('view_studentinvolvement', 'tuition'),
        ('view_resultapproval', 'tuition'),
    }
    
    # Check if groups exist
    print("\n1. CHECKING GROUPS EXISTENCE")
    print("-" * 80)
    
    groups_exist = True
    professor_group = None
    student_group = None
    
    try:
        professor_group = Group.objects.get(name='Professor')
        print("[OK] Professor group exists")
    except Group.DoesNotExist:
        print("[FAIL] Professor group NOT found")
        groups_exist = False
    
    try:
        student_group = Group.objects.get(name='Student')
        print("[OK] Student group exists")
    except Group.DoesNotExist:
        print("[FAIL] Student group NOT found")
        groups_exist = False
    
    if not groups_exist:
        print("\n[ERROR] Required groups not found!")
        return False
    
    # Check permissions for Professor group
    print("\n2. PROFESSOR GROUP PERMISSIONS VERIFICATION")
    print("-" * 80)
    
    professor_actual_perms = set()
    for perm in professor_group.permissions.all():
        perm_tuple = (perm.codename, perm.content_type.app_label)
        professor_actual_perms.add(perm_tuple)
    
    print(f"Total permissions assigned: {len(professor_actual_perms)}")
    print(f"Expected permissions: {len(expected_professor_perms)}")
    
    missing_prof = expected_professor_perms - professor_actual_perms
    extra_prof = professor_actual_perms - expected_professor_perms
    
    if missing_prof:
        print(f"\n[WARN] Missing permissions ({len(missing_prof)}):")
        for codename, app in sorted(missing_prof):
            print(f"  - {app}.{codename}")
    
    if extra_prof:
        print(f"\n[WARN] Extra permissions ({len(extra_prof)}):")
        for codename, app in sorted(extra_prof):
            print(f"  + {app}.{codename}")
    
    professor_ok = len(missing_prof) == 0 and len(extra_prof) == 0
    
    if professor_ok:
        print("\n[OK] All Professor permissions are correct!")
    else:
        print(f"\n[FAIL] Professor permissions have issues: {len(missing_prof)} missing, {len(extra_prof)} extra")
    
    # Check permissions for Student group
    print("\n3. STUDENT GROUP PERMISSIONS VERIFICATION")
    print("-" * 80)
    
    student_actual_perms = set()
    for perm in student_group.permissions.all():
        perm_tuple = (perm.codename, perm.content_type.app_label)
        student_actual_perms.add(perm_tuple)
    
    print(f"Total permissions assigned: {len(student_actual_perms)}")
    print(f"Expected permissions: {len(expected_student_perms)}")
    
    missing_student = expected_student_perms - student_actual_perms
    extra_student = student_actual_perms - expected_student_perms
    
    if missing_student:
        print(f"\n[WARN] Missing permissions ({len(missing_student)}):")
        for codename, app in sorted(missing_student):
            print(f"  - {app}.{codename}")
    
    if extra_student:
        print(f"\n[WARN] Extra permissions ({len(extra_student)}):")
        for codename, app in sorted(extra_student):
            print(f"  + {app}.{codename}")
    
    student_ok = len(missing_student) == 0 and len(extra_student) == 0
    
    if student_ok:
        print("\n[OK] All Student permissions are correct!")
    else:
        print(f"\n[FAIL] Student permissions have issues: {len(missing_student)} missing, {len(extra_student)} extra")
    
    # Display permissions by app
    print("\n4. PERMISSIONS BREAKDOWN BY APP")
    print("-" * 80)
    
    print("\nProfessor Group - By App:")
    prof_by_app = defaultdict(list)
    for perm in professor_group.permissions.all():
        prof_by_app[perm.content_type.app_label].append(perm.codename)
    
    for app in sorted(prof_by_app.keys()):
        perms = sorted(prof_by_app[app])
        print(f"  {app}: {len(perms)} permissions")
        for p in perms:
            print(f"    - {p}")
    
    print("\nStudent Group - By App:")
    student_by_app = defaultdict(list)
    for perm in student_group.permissions.all():
        student_by_app[perm.content_type.app_label].append(perm.codename)
    
    for app in sorted(student_by_app.keys()):
        perms = sorted(student_by_app[app])
        print(f"  {app}: {len(perms)} permissions")
        for p in perms:
            print(f"    - {p}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    all_ok = professor_ok and student_ok
    
    if all_ok:
        print("[OK] ALL CHECKS PASSED!")
        print("[OK] Groups are properly configured with correct permissions")
        print("[OK] System is ready for user assignment")
        return True
    else:
        print("[FAIL] SOME CHECKS FAILED!")
        if not professor_ok:
            print(f"  - Professor group has {len(missing_prof)} missing and {len(extra_prof)} extra permissions")
        if not student_ok:
            print(f"  - Student group has {len(missing_student)} missing and {len(extra_student)} extra permissions")
        return False


if __name__ == '__main__':
    success = verify_groups_and_permissions()
    sys.exit(0 if success else 1)
