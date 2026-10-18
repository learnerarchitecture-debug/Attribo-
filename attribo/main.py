"""
Application entry point.
(c) 2026 Attribo. All rights reserved.
"""
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from . import APP_NAME, VENDOR
from .storage import db
from .storage.settings import load_settings
from .theme import QSS
from .ui.main_window import MainWindow


def main() -> int:
    db.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(VENDOR)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    app.setFont(QFont("Segoe UI", 10))

    settings = load_settings()
    window = MainWindow(settings)
    window.show()
    return app.exec()
