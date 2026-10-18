"""
Generic background worker for one-shot tasks (model download, network
validation runs). Keeps the UI responsive.

(c) 2026 Attribo. All rights reserved.
"""
from PySide6.QtCore import QThread, Signal


class FuncWorker(QThread):
    progress = Signal(int, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, func, parent=None):
        super().__init__(parent)
        self._func = func
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:  # noqa: D102
        try:
            result = self._func(
                progress=lambda pct, msg: self.progress.emit(int(pct), msg),
                cancel=lambda: self._cancel,
            )
            self.done.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
