from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create default groups (Professor and Student) with appropriate permissions'

    def handle(self, *args, **options):
        # Define groups and their permissions
        # Format: (permission_codename, app_label)
        groups_permissions = {
            'Professor': [
                # ===== QUESTIONS APP - FULL CRUD =====
                # Main question and exam models
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
                
                # Question enhancements
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
                
                # Exam assignments and security features
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
                
                # ===== FACULTY APP =====
                ('add_facultyinfo', 'faculty'),
                ('change_facultyinfo', 'faculty'),
                ('delete_facultyinfo', 'faculty'),
                ('view_facultyinfo', 'faculty'),
                
                # ===== COURSE APP =====
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
                
                # ===== RESULT PROCESSING APP =====
                ('add_configmarks', 'resultprocessing'),
                ('change_configmarks', 'resultprocessing'),
                ('delete_configmarks', 'resultprocessing'),
                ('view_configmarks', 'resultprocessing'),
                
                ('view_score', 'resultprocessing'),
                ('view_student', 'resultprocessing'),
                ('view_program', 'resultprocessing'),
                
                # ===== NOTIFICATIONS APP =====
                ('view_notification', 'notifications'),
                ('view_notificationpreference', 'notifications'),
            ],
            'Student': [
                # ===== STUDENT APP - Full access to own data =====
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
                
                # ===== QUESTIONS APP - View only =====
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
                
                # ===== COURSE APP - View only =====
                ('view_course', 'course'),
                ('view_session', 'course'),
                ('view_courseregistration', 'course'),
                ('view_grade', 'course'),
                ('view_studentacceptance', 'course'),
                
                # ===== RESULT PROCESSING - View own results =====
                ('view_score', 'resultprocessing'),
                
                # ===== STUDENT PREFERENCES =====
                ('add_studentpreferencemodel', 'studentPreferences'),
                ('change_studentpreferencemodel', 'studentPreferences'),
                ('delete_studentpreferencemodel', 'studentPreferences'),
                ('view_studentpreferencemodel', 'studentPreferences'),
                
                # ===== NOTIFICATIONS - Manage own preferences =====
                ('add_notificationpreference', 'notifications'),
                ('change_notificationpreference', 'notifications'),
                ('view_notificationpreference', 'notifications'),
                ('view_notification', 'notifications'),
                
                # ===== TUITION/WALLET =====
                ('add_studentwallet', 'tuition'),
                ('change_studentwallet', 'tuition'),
                ('view_studentwallet', 'tuition'),
                
                ('view_librarybook', 'tuition'),
                ('view_studentinvolvement', 'tuition'),
                ('view_resultapproval', 'tuition'),
            ]
        }

        for group_name, permissions in groups_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {group_name}')
                )
            else:
                self.stdout.write(f'Group "{group_name}" already exists')
            
            # Add permissions to group
            permissions_to_add = []
            for perm_codename, app_label in permissions:
                if not ContentType.objects.filter(app_label=app_label).exists():
                    # App not migrated yet; skip silently and let later post_migrate
                    # calls assign these permissions once the app is ready.
                    continue

                try:
                    permission = Permission.objects.get(
                        codename=perm_codename,
                        content_type__app_label=app_label
                    )
                    permissions_to_add.append(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Permission "{perm_codename}" not found in app "{app_label}"'
                        )
                    )
            
            # Add all found permissions to the group
            if permissions_to_add:
                group.permissions.add(*permissions_to_add)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  → Added {len(permissions_to_add)} permissions to {group_name}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Groups and permissions setup completed successfully!')
        )
