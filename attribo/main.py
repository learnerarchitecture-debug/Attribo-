"""
Application entry point.

Supports the shell integration "Scan with Attribo": a file passed as
`--scan <path>` (or a bare path) is opened and scanned automatically.
(c) 2026 Attribo. All rights reserved.
"""
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from . import APP_NAME, VENDOR
from .storage import db
from .storage.settings import load_settings
from .theme import stylesheet
from .ui.main_window import MainWindow

SUPPORTED_EXTS = {".docx", ".pdf", ".txt", ".md", ".rtf", ".odt"}


def _scan_target(argv: list) -> str:
    """A document passed via '--scan PATH' or as a bare path, else ''."""
    if "--scan" in argv:
        index = argv.index("--scan")
        if index + 1 < len(argv):
            candidate = Path(argv[index + 1])
            if candidate.exists():
                return str(candidate)
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        candidate = Path(arg)
        if candidate.exists() and candidate.suffix.lower() in SUPPORTED_EXTS:
            return str(candidate)
    return ""


def main() -> int:
    db.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(VENDOR)
    app.setStyle("Fusion")
    settings = load_settings()
    app.setStyleSheet(stylesheet(str(settings.get("theme", "dark"))))
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow(settings)
    window.show()

    target = _scan_target(sys.argv)
    if target:
        QTimer.singleShot(500, lambda: window.open_document(target))

    return app.exec()
