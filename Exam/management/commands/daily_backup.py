"""Daily backup management command."""

import os
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    help = 'Perform daily full backup (DB + media files)'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default='backups', help='Backup output directory')

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        timestamp = subprocess.check_output('date /t', shell=True).decode().strip().replace('/', '-').replace(' ', '_').replace(':', '-')
        
        # SQLite DB backup (dev)
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            db_path = settings.DATABASES['default']['NAME']
            backup_db = f"{output_dir}/db_{timestamp}.sqlite3"
            self.stdout.write(f"Backing up DB to {backup_db}")
            with open(backup_db, 'wb') as f:
                with open(db_path, 'rb') as source:
                    f.write(source.read())
        
        # Media backup (tar.gz)
        media_backup = f"{output_dir}/media_{timestamp}.tar.gz"
        self.stdout.write(f"Backing up media to {media_backup}")
        subprocess.call(f'tar -czf "{media_backup}" -C "{settings.MEDIA_ROOT}" .', shell=True, stdout=subprocess.DEVNULL)
        
        self.stdout.write(self.style.SUCCESS(f'Backup complete: {output_dir}/'))

