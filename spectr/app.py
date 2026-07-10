# Application entry point — creates the QApplication and opens the main window.
# Called by main.py (python main.py) and spectr/__main__.py (python -m spectr).

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from spectr.ui.main_window import MainWindow

log = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("SPECTR")

    window = MainWindow()
    window.show()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
