"""
Testing custom django management commands
"""

from unittest.mock import patch
from psycopg import OperationalError as PsycopgError
from django.test import SimpleTestCase
from django.db import OperationalError
from django.core.management import call_command


@patch("core.management.commands.wait_for_db.Command.check")
class CommandTests(SimpleTestCase):
    """Test Commands"""

    def test_wait_for_db_ready(self, patched_check):
        """Test: Wait for db if db is ready"""
        patched_check.return_value = True
        call_command("wait_for_db")

        patched_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waititng for the database when getting OperationalError"""
        patched_check.side_effect = (
            [PsycopgError] * 2 + [OperationalError] * 3 + [True]
        )  # noqa

        call_command("wait_for_db")
        self.assertEqual(patched_sleep.call_count, 5)
        self.assertEqual(patched_check.call_count, 6)
        patched_check.assert_called_with(databases=["default"])
