import ctypes
import sys


ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "Global\\RadiologyAutoReporterUnified"


class SingleInstanceGuard:
    def __init__(self, handle=None, already_running=False, close_handle=None):
        self.handle = handle
        self.already_running = already_running
        self._close_handle = close_handle

    def close(self):
        if self.handle:
            if self._close_handle is not None:
                self._close_handle(self.handle)
            self.handle = None


def acquire_single_instance(mutex_name=MUTEX_NAME):
    if sys.platform != "win32":
        return SingleInstanceGuard()

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, mutex_name)
    already_running = kernel32.GetLastError() == ERROR_ALREADY_EXISTS
    return SingleInstanceGuard(
        handle=handle,
        already_running=already_running,
        close_handle=kernel32.CloseHandle,
    )
