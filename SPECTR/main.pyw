#!/usr/bin/env python3
import sys
import os
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter
except ImportError:
    print("Error: tkinter is required. Install python-tk package.")
    sys.exit(1)

from core.app import App


def main():
    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        app.shutdown()
    finally:
        os._exit(0)


if __name__ == "__main__":
    main()
