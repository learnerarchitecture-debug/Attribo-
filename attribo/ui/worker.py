"""
Background scan worker (QThread).

(c) 2026 Attribo. All rights reserved.
"""
from PySide6.QtCore import QThread, Signal

from ..core.pipeline import run_scan


class ScanWorker(QThread):
    progress = Signal(int, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, path: str, settings: dict, parent=None):
        super().__init__(parent)
        self.path = path
        self.settings = dict(settings)
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:  # noqa: D102
        try:
            result = run_scan(
                self.path,
                self.settings,
                progress=lambda pct, msg: self.progress.emit(int(pct), msg),
                cancel=lambda: self._cancel,
            )
            self.done.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class BatchWorker(QThread):
    progress = Signal(int, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, paths: list, settings: dict, out_dir: str, parent=None):
        super().__init__(parent)
        self.paths = list(paths)
        self.settings = dict(settings)
        self.out_dir = out_dir
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:  # noqa: D102
        from ..core.batch import run_batch

        try:
            results = run_batch(
                self.paths,
                self.settings,
                self.out_dir,
                progress=lambda i, total, msg: self.progress.emit(
                    int(100 * i / max(total, 1)), f"[{i}/{total}] {msg}"
                ),
                cancel=lambda: self._cancel,
            )
            self.done.emit(results)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
