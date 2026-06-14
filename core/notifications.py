"""Toast notification system for SPECTR plugins."""

import tkinter as tk

LEVELS = {
    "info": "#00d4aa",
    "success": "#00d4aa",
    "warning": "#ffaa00",
    "error": "#ff4444",
}


class NotificationManager:
    """Manages toast notifications on the overlay root window."""

    def __init__(self, root, scale_factor=1.0):
        self._root = root
        self._sf = scale_factor
        self._queue = []
        self._active = None
        self._margin = max(8, round(12 * scale_factor))

    def show(self, message, level="info", duration_ms=3000):
        """Show a toast notification. Levels: info, success, warning, error."""
        color = LEVELS.get(level, LEVELS["info"])
        self._queue.append((message, color, duration_ms))
        if self._active is None:
            self._pop()

    def _pop(self):
        if not self._queue:
            self._active = None
            return
        message, color, duration_ms = self._queue.pop(0)
        self._show_toast(message, color, duration_ms)

    def _show_toast(self, message, color, duration_ms):
        sf = self._sf
        pad_x = max(6, round(10 * sf))
        pad_y = max(4, round(6 * sf))
        font_size = max(8, round(10 * sf))
        font = ("Consolas", font_size)

        toast = tk.Toplevel(self._root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=color)

        lbl = tk.Label(
            toast, text=message, font=font,
            bg=color, fg="#000000", padx=pad_x, pady=pad_y,
            wraplength=max(200, round(350 * sf)),
        )
        lbl.pack()

        toast.update_idletasks()
        tw = toast.winfo_width()
        th = toast.winfo_height()
        sw = self._root.winfo_screenwidth()
        x = sw - tw - self._margin
        y = self._margin

        if self._active is not None:
            try:
                old_y = self._active.winfo_y()
                y = old_y + self._active.winfo_height() + max(4, round(6 * sf))
            except Exception:
                pass

        toast.geometry(f"+{x}+{y}")
        self._active = toast

        def dismiss():
            try:
                toast.destroy()
            except Exception:
                pass
            self._active = None
            try:
                self._root.after(100, self._pop)
            except Exception:
                pass

        self._root.after(duration_ms, dismiss)
