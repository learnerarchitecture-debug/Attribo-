"""
Drag & drop intake card.

(c) 2026 Attribo. All rights reserved.
"""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout

FILE_FILTER = "Documents (*.docx *.pdf *.txt *.md *.rtf *.odt);;All files (*.*)"


class DropZone(QFrame):
    fileSelected = Signal(str)

    IDLE_QSS = (
        "QFrame#DropZone { background: #0F141C; border: 2px dashed #2A3441; border-radius: 16px; }"
    )
    HOVER_QSS = (
        "QFrame#DropZone { background: #101827; border: 2px dashed #5B8CFF; border-radius: 16px; }"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(170)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        self.icon = QLabel("\u2b06")
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setStyleSheet("font-size: 30px; color: #5B8CFF;")
        self.title = QLabel("Drag & drop your document here")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.sub = QLabel("or click to browse \u2014 DOCX \u00b7 PDF \u00b7 TXT \u00b7 MD \u00b7 RTF \u00b7 ODT")
        self.sub.setAlignment(Qt.AlignCenter)
        self.sub.setObjectName("Muted")
        self.sub.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(self.icon)
        layout.addWidget(self.title)
        layout.addWidget(self.sub)
        layout.addStretch(1)

        self.setStyleSheet(self.IDLE_QSS)

    # -- state ---------------------------------------------------------
    def set_file(self, path: str) -> None:
        p = Path(path)
        self.title.setText(p.name)
        self.sub.setText(str(p.parent))

    def reset(self) -> None:
        self.title.setText("Drag & drop your document here")
        self.sub.setText("or click to browse \u2014 DOCX \u00b7 PDF \u00b7 TXT \u00b7 MD \u00b7 RTF \u00b7 ODT")

    # -- drag & drop ---------------------------------------------------
    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.HOVER_QSS)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self.IDLE_QSS)

    def dropEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self.IDLE_QSS)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.fileSelected.emit(path)
                event.acceptProposedAction()

    # -- click to browse -----------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select document", "", FILE_FILTER
            )
            if path:
                self.fileSelected.emit(path)
