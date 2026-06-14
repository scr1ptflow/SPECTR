#!/usr/bin/env python3
import sys
import os
import threading
import logging
import traceback

if getattr(sys, 'frozen', False):
    _base = os.path.dirname(os.path.abspath(sys.executable))
else:
    _base = os.path.dirname(os.path.abspath(__file__))

_log_path = os.path.join(_base, "spectr.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(_log_path, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

sys.path.insert(0, _base)

try:
    import tkinter
except ImportError:
    print("Error: tkinter is required. Install python-tk package.")
    sys.exit(1)

from core.app import App

logger = logging.getLogger(__name__)


def _force_exit():
    """Force exit if sys.exit() hangs (e.g., tkinter mainloop stuck)."""
    os._exit(0)


def _show_crash_dialog(tb_text):
    """Show a crash dialog with the traceback."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror(
            "SPECTR — Crash",
            f"An unexpected error occurred:\n\n{tb_text[-2000:]}"
        )
        root.destroy()
    except Exception:
        pass


def main():
    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        app.shutdown()
    except Exception:
        tb = traceback.format_exc()
        logger.error(f"Unhandled exception:\n{tb}")
        _show_crash_dialog(tb)
        raise
    finally:
        timer = threading.Timer(2.0, _force_exit)
        timer.daemon = True
        timer.start()
        sys.exit(0)


if __name__ == "__main__":
    main()
