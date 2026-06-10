import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger(__name__)

USER32 = ctypes.windll.user32
ENUM_WINDOWS = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

WINDOW_TITLES = [
    "Elite Dangerous",
    "Elite - Dangerous",
    "EliteDangerous64",
]

RECT = ctypes.wintypes.RECT


class GameWindow:
    def __init__(self):
        self.hwnd = None
        self.rect = None
        self.focused = False
        self._enum_proc = ENUM_WINDOWS(self._enum_callback)

    def _enum_callback(self, hwnd, l_param):
        length = USER32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        USER32.GetWindowTextW(hwnd, buf, length)
        title = buf.value
        for t in WINDOW_TITLES:
            if t in title:
                if USER32.IsWindowVisible(hwnd):
                    self.hwnd = hwnd
                    return False
        return True

    def find(self):
        self.hwnd = None
        USER32.EnumWindows(self._enum_proc, 0)
        if self.hwnd:
            logger.debug(f"Found game window: {self.hwnd}")
        return self.hwnd is not None

    def get_rect(self):
        if not self.hwnd:
            return None
        r = RECT()
        if USER32.GetWindowRect(self.hwnd, ctypes.byref(r)):
            self.rect = {
                "left": r.left,
                "top": r.top,
                "right": r.right,
                "bottom": r.bottom,
                "width": r.right - r.left,
                "height": r.bottom - r.top,
            }
            return self.rect
        return None

    def is_focused(self):
        if not self.hwnd:
            return False
        foreground = USER32.GetForegroundWindow()
        self.focused = foreground == self.hwnd
        return self.focused

    def poll(self):
        if not self.hwnd:
            self.find()
        if not self.hwnd:
            self.rect = None
            return None, False
        old_rect = self.rect
        rect = self.get_rect()
        if not rect:
            self.hwnd = None
            self.rect = None
            return None, False
        changed = bool(rect != old_rect)
        return rect, changed
