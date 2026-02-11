"""
Django command to wait for db to be available
"""

from django.core.management.base import BaseCommand
import time
from psycopg import OperationalError as PsycopgError
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for db"""

    def handle(self, *args, **options):
        """Entrypoint for command"""
        self.stdout.write("Waiting for database...")
        db_up = False
        while db_up is False:
            try:
                self.check(databases=["default"])
                db_up = True
            except (OperationalError, PsycopgError):
                self.stdout.write("Database is not available, wait 1 second")
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS("Database available!"))
