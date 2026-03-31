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
                # Questions app - Full CRUD
                ('add_question_db', 'questions'),
                ('change_question_db', 'questions'),
                ('delete_question_db', 'questions'),
                ('view_question_db', 'questions'),
                
                # Question Paper - Full CRUD
                ('add_question_paper', 'questions'),
                ('change_question_paper', 'questions'),
                ('delete_question_paper', 'questions'),
                ('view_question_paper', 'questions'),
                
                # Exam Model - Full CRUD
                ('add_exam_model', 'questions'),
                ('change_exam_model', 'questions'),
                ('delete_exam_model', 'questions'),
                ('view_exam_model', 'questions'),
                
                # Faculty Info - Full CRUD
                ('add_facultyinfo', 'faculty'),
                ('change_facultyinfo', 'faculty'),
                ('delete_facultyinfo', 'faculty'),
                ('view_facultyinfo', 'faculty'),
                
                # Course - Full CRUD
                ('add_course', 'course'),
                ('change_course', 'course'),
                ('delete_course', 'course'),
                ('view_course', 'course'),
                
                # Course Session
                ('add_session', 'course'),
                ('change_session', 'course'),
                ('delete_session', 'course'),
                ('view_session', 'course'),
            ],
            'Student': [
                # Student Info - Create and modify own
                ('add_studentinfo', 'student'),
                ('change_studentinfo', 'student'),
                ('view_studentinfo', 'student'),
                
                # Student Exam - Create and take exams
                ('add_stu_question', 'student'),
                ('change_stu_question', 'student'),
                ('view_stu_question', 'student'),
                
                # Student Exam Database
                ('add_stuexam_db', 'student'),
                ('change_stuexam_db', 'student'),
                ('view_stuexam_db', 'student'),
                
                # Student Results
                ('add_sturesults_db', 'student'),
                ('view_sturesults_db', 'student'),
                
                # Question Paper - View only
                ('view_question_paper', 'questions'),
                ('view_question_db', 'questions'),
                ('view_exam_model', 'questions'),
                
                # Course - View only
                ('view_course', 'course'),
                ('view_session', 'course'),
                
                # Student Preferences
                ('add_studentpreference', 'studentPreferences'),
                ('change_studentpreference', 'studentPreferences'),
                ('view_studentpreference', 'studentPreferences'),
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
