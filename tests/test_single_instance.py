import unittest
from unittest.mock import patch

import single_instance


class FakeKernel32:
    def __init__(self, last_error):
        self.last_error = last_error
        self.closed = []

    def CreateMutexW(self, security, initial_owner, name):
        self.name = name
        return 1234

    def GetLastError(self):
        return self.last_error

    def CloseHandle(self, handle):
        self.closed.append(handle)


class FakeWindll:
    def __init__(self, kernel32):
        self.kernel32 = kernel32


class TestSingleInstance(unittest.TestCase):
    def test_windows_mutex_detects_duplicate_instance(self):
        kernel32 = FakeKernel32(single_instance.ERROR_ALREADY_EXISTS)

        with patch.object(single_instance.sys, "platform", "win32"):
            with patch.object(single_instance.ctypes, "windll", FakeWindll(kernel32), create=True):
                guard = single_instance.acquire_single_instance()

        self.assertTrue(guard.already_running)
        self.assertEqual(kernel32.name, single_instance.MUTEX_NAME)

        guard.close()
        self.assertEqual(kernel32.closed, [1234])

    def test_non_windows_is_noop(self):
        with patch.object(single_instance.sys, "platform", "linux"):
            guard = single_instance.acquire_single_instance()

        self.assertFalse(guard.already_running)
        self.assertIsNone(guard.handle)


if __name__ == "__main__":
    unittest.main()
