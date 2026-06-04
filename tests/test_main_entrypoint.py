import unittest
from unittest.mock import patch

import main as app_main


class FakeGuard:
    def __init__(self, already_running=False):
        self.already_running = already_running
        self.closed = False

    def close(self):
        self.closed = True


class TestMainEntrypoint(unittest.TestCase):
    def test_duplicate_instance_exits_without_creating_app_manager(self):
        guard = FakeGuard(already_running=True)

        with patch.object(app_main, "acquire_single_instance", return_value=guard):
            with patch.object(app_main, "AppManager") as app_manager:
                exit_code = app_main.main()

        self.assertEqual(exit_code, 0)
        app_manager.assert_not_called()
        self.assertFalse(guard.closed)

    def test_single_instance_guard_is_released_after_app_exits(self):
        guard = FakeGuard(already_running=False)

        class FakeManager:
            def run(self):
                return None

        with patch.object(app_main, "acquire_single_instance", return_value=guard):
            with patch.object(app_main, "AppManager", return_value=FakeManager()):
                exit_code = app_main.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(guard.closed)


if __name__ == "__main__":
    unittest.main()
