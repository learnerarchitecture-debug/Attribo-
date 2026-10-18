"""
Main window: drop zone, scan options, results tabs, exports, automation.

(c) 2026 Attribo. All rights reserved.
"""
from html import escape as html_escape
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .drop_zone import DropZone
from .func_worker import FuncWorker
from .gauges import ScoreRing
from .settings_dialog import SettingsDialog
from .worker import BatchWorker, ScanWorker
from .. import APP_NAME, COPYRIGHT, __version__
from ..core import batch as batch_mod
from ..core import fixcite, updater
from ..licensing.keycheck import verify_key
from ..report import findings, highlight, pdf_builder, word_export
from ..storage import db
from ..storage.settings import APP_DIR, save_settings
from ..theme import ACCENT, MATCH_COLORS, MATCH_LABELS, SUCCESS, WARN

WATCH_OUT_DIR = APP_DIR / "Watched Reports"


def h(value) -> str:
    return html_escape(str(value or ""))


class MainWindow(QMainWindow):
    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self.current_file = None
        self.result = None
        self.worker = None
        self.batch_worker = None
        self.watch_worker = None
        self.func_worker = None
        self._result_matches = []
        self._gaps = []
        self._candidates = []
        self._ref_results = []
        self._watch_queue = []
        self._watch_seen = {}
        self._watch_out = str(WATCH_OUT_DIR)
        self._batch_out = ""
        self._update_info = None
        self._update_worker = None
        self._downloaded_update = ""
        self.setWindowTitle(f"{APP_NAME} \u2014 v{__version__}")
        self.resize(1360, 880)
        self.setAcceptDrops(True)
        self._build_ui()
        self._refresh_license_label()
        self._refresh_history()
        self._init_watch()
        self._init_updates()

    # ================================================================ UI ==
    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- header ----------------------------------------------------
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(64)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        brand = QLabel("Attribo")
        brand.setObjectName("BrandText2")
        version = QLabel(f"v{__version__} \u00b7 local-first screening")
        version.setObjectName("Muted")
        self.license_lbl = QLabel("")
        self.license_lbl.setObjectName("Muted")
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self._open_settings)
        self.update_btn = QPushButton("")
        self.update_btn.setObjectName("UpdateBanner")
        self.update_btn.setVisible(False)
        self.update_btn.clicked.connect(self._show_update_dialog)
        hl.addWidget(brand)
        hl.addSpacing(12)
        hl.addWidget(version)
        hl.addStretch(1)
        hl.addWidget(self.update_btn)
        hl.addWidget(self.license_lbl)
        hl.addWidget(settings_btn)
        outer.addWidget(header)

        # ---- body ------------------------------------------------------
        body = QWidget()
        bl = QHBoxLayout(body)
        bl.setContentsMargins(16, 16, 16, 8)
        splitter = QSplitter(Qt.Horizontal)
        bl.addWidget(splitter)
        outer.addWidget(body, 1)

        # left panel
        left = QFrame()
        left.setObjectName("Card")
        left.setMinimumWidth(390)
        left.setMaximumWidth(470)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 16, 16, 16)
        ll.setSpacing(10)

        self.drop_zone = DropZone()
        self.drop_zone.fileSelected.connect(self._select_file)
        ll.addWidget(self.drop_zone)

        options = QLabel("Scan options")
        options.setObjectName("H2")
        ll.addWidget(options)

        self.chk_web = QCheckBox("Web sources (search APIs)")
        self.chk_web.setChecked(bool(self.settings.get("enable_web", True)))
        self.chk_academic = QCheckBox("Academic sources (OpenAlex / Crossref)")
        self.chk_academic.setChecked(bool(self.settings.get("enable_academic", True)))
        self.chk_ai = QCheckBox("AI-likelihood analysis (local)")
        self.chk_ai.setChecked(bool(self.settings.get("enable_ai", True)))
        self.chk_quotes = QCheckBox("Exclude quoted blocks from scoring")
        self.chk_quotes.setChecked(bool(self.settings.get("exclude_quotes", False)))
        ll.addWidget(self.chk_web)
        ll.addWidget(self.chk_academic)
        ll.addWidget(self.chk_ai)
        ll.addWidget(self.chk_quotes)

        self.chk_archive = QCheckBox("Compare against local folder (archive)")
        self.chk_archive.setChecked(bool(self.settings.get("enable_archive", False)))
        ll.addWidget(self.chk_archive)

        arow = QHBoxLayout()
        self.archive_btn = QPushButton("Choose folder...")
        self.archive_btn.clicked.connect(self._choose_archive_folder)
        self.archive_lbl = QLabel("")
        self.archive_lbl.setObjectName("Muted")
        self.archive_lbl.setWordWrap(True)
        arow.addWidget(self.archive_btn)
        arow.addWidget(self.archive_lbl, 1)
        ll.addLayout(arow)
        self._refresh_archive_label()

        qrow = QHBoxLayout()
        qlabel = QLabel("Search queries:")
        qlabel.setObjectName("Muted")
        self.spin_queries = QSpinBox()
        self.spin_queries.setRange(2, 50)
        self.spin_queries.setValue(int(self.settings.get("max_queries", 12)))
        qrow.addWidget(qlabel)
        qrow.addWidget(self.spin_queries)
        qrow.addStretch(1)
        ll.addLayout(qrow)

        srow = QHBoxLayout()
        self.start_btn = QPushButton("Start Scan")
        self.start_btn.setObjectName("Primary")
        self.start_btn.clicked.connect(self._start_scan)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_scan)
        srow.addWidget(self.start_btn, 1)
        srow.addWidget(self.cancel_btn)
        ll.addLayout(srow)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        ll.addWidget(self.progress)

        self.status_lbl = QLabel("Ready. Drop a document or click the drop area.")
        self.status_lbl.setObjectName("Muted")
        self.status_lbl.setWordWrap(True)
        ll.addWidget(self.status_lbl)

        automation = QLabel("Automation")
        automation.setObjectName("H2")
        ll.addWidget(automation)

        brow = QHBoxLayout()
        self.batch_btn = QPushButton("Batch scan folder...")
        self.batch_btn.clicked.connect(self._start_batch)
        brow.addWidget(self.batch_btn)
        brow.addStretch(1)
        ll.addLayout(brow)

        self.chk_watch = QCheckBox("Watch folder for new documents")
        self.chk_watch.setChecked(bool(self.settings.get("watch_enabled", False)))
        self.chk_watch.toggled.connect(self._toggle_watch)
        ll.addWidget(self.chk_watch)

        wrow = QHBoxLayout()
        self.watch_btn = QPushButton("Folder...")
        self.watch_btn.clicked.connect(self._choose_watch_folder)
        self.watch_lbl = QLabel("")
        self.watch_lbl.setObjectName("Muted")
        self.watch_lbl.setWordWrap(True)
        wrow.addWidget(self.watch_btn)
        wrow.addWidget(self.watch_lbl, 1)
        ll.addLayout(wrow)
        self._refresh_watch_label()

        ll.addStretch(1)

        keys_hint = QLabel(
            "Tip: add free API keys in Settings to enable web checking "
            "(see docs/API_KEYS.md)."
        )
        keys_hint.setObjectName("Muted")
        keys_hint.setWordWrap(True)
        ll.addWidget(keys_hint)

        splitter.addWidget(left)

        # right tabs
        self.tabs = QTabWidget()
        self._build_summary_tab()
        self._build_matches_tab()
        self._build_fixcite_tab()
        self._build_cite_tab()
        self._build_refs_tab()
        self._build_cert_tab()
        self._build_history_tab()
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(1, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(
            f"{COPYRIGHT} \u00b7 Your document never leaves this PC."
        )

    def _build_summary_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        rings = QHBoxLayout()
        self.ring_sim = ScoreRing("Similarity", ACCENT)
        self.ring_para = ScoreRing("Paraphrase (beta)", WARN)
        self.ring_ai = ScoreRing("AI-likelihood (beta)", "#A78BFA")
        self.ring_int = ScoreRing("Integrity", SUCCESS)
        for ring in (self.ring_sim, self.ring_para, self.ring_ai, self.ring_int):
            rings.addWidget(ring)
        layout.addLayout(rings)
        self.summary_info = QTextBrowser()
        self.summary_info.setOpenExternalLinks(True)
        self.summary_info.setPlaceholderText("Scan results will appear here.")
        layout.addWidget(self.summary_info, 1)
        self.tabs.addTab(page, "Summary")

    def _build_matches_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.matches_table = QTableWidget(0, 4)
        self.matches_table.setHorizontalHeaderLabels(
            ["Type", "Tokens", "Source", "Matched passage"]
        )
        header = self.matches_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.matches_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.matches_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.matches_table.setAlternatingRowColors(True)
        self.matches_table.itemSelectionChanged.connect(self._show_match_detail)
        layout.addWidget(self.matches_table, 2)
        self.match_detail = QTextBrowser()
        self.match_detail.setOpenExternalLinks(True)
        self.match_detail.setPlaceholderText(
            "Select a match above to see your passage next to the source passage."
        )
        layout.addWidget(self.match_detail, 1)
        self.tabs.addTab(page, "Matches")

    def _build_fixcite_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.fix_table = QTableWidget(0, 4)
        self.fix_table.setHorizontalHeaderLabels(["Type", "Source", "Passage", "Suggested fix"])
        header = self.fix_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.fix_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fix_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fix_table.setAlternatingRowColors(True)
        layout.addWidget(self.fix_table, 1)

        row = QHBoxLayout()
        copy_btn = QPushButton("Copy reference (APA-style)")
        copy_btn.clicked.connect(self._copy_reference)
        open_btn = QPushButton("Open source in browser")
        open_btn.clicked.connect(self._open_source)
        row.addWidget(copy_btn)
        row.addWidget(open_btn)
        row.addStretch(1)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        self.btn_findings = QPushButton("Export findings (HTML)")
        self.btn_findings.setEnabled(False)
        self.btn_findings.clicked.connect(self._export_findings)
        self.btn_highlight = QPushButton("Export highlighted copy (HTML)")
        self.btn_highlight.setEnabled(False)
        self.btn_highlight.clicked.connect(self._export_highlight)
        self.btn_word = QPushButton("Export Word review copy (.docx)")
        self.btn_word.setEnabled(False)
        self.btn_word.clicked.connect(self._export_word)
        row2.addWidget(self.btn_findings)
        row2.addWidget(self.btn_highlight)
        row2.addWidget(self.btn_word)
        row2.addStretch(1)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.btn_worklist = QPushButton("Export Fix & Cite worklist (.docx)")
        self.btn_worklist.setObjectName("Primary")
        self.btn_worklist.setEnabled(False)
        self.btn_worklist.clicked.connect(self._export_worklist)
        self.btn_copy_fix = QPushButton("Copy fix for selected flag")
        self.btn_copy_fix.clicked.connect(self._copy_fix)
        row3.addWidget(self.btn_worklist)
        row3.addWidget(self.btn_copy_fix)
        row3.addStretch(1)
        layout.addLayout(row3)
        self.tabs.addTab(page, "Fix && Cite")

    def _build_cite_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        info = QLabel(
            "Sentences that make claims without a citation nearby. Select a gap and "
            "search OpenAlex / Crossref for candidate sources to cite."
        )
        info.setObjectName("Muted")
        info.setWordWrap(True)
        layout.addWidget(info)
        self.gap_table = QTableWidget(0, 3)
        self.gap_table.setHorizontalHeaderLabels(["#", "Why flagged", "Sentence"])
        gheader = self.gap_table.horizontalHeader()
        gheader.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        gheader.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        gheader.setSectionResizeMode(2, QHeaderView.Stretch)
        self.gap_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.gap_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.gap_table.setAlternatingRowColors(True)
        layout.addWidget(self.gap_table, 2)

        grow = QHBoxLayout()
        self.btn_gap_sel = QPushButton("Find sources for selected gap")
        self.btn_gap_sel.clicked.connect(self._find_sources_selected)
        self.btn_gap_top = QPushButton("Find sources for top 3 gaps")
        self.btn_gap_top.clicked.connect(self._find_top_gaps)
        grow.addWidget(self.btn_gap_sel)
        grow.addWidget(self.btn_gap_top)
        grow.addStretch(1)
        layout.addLayout(grow)

        self.cand_table = QTableWidget(0, 3)
        self.cand_table.setHorizontalHeaderLabels(["Gap", "Suggested source", "Link / DOI"])
        cheader = self.cand_table.horizontalHeader()
        cheader.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cheader.setSectionResizeMode(1, QHeaderView.Stretch)
        cheader.setSectionResizeMode(2, QHeaderView.Stretch)
        self.cand_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cand_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cand_table.setAlternatingRowColors(True)
        self.cand_table.itemDoubleClicked.connect(self._open_candidate)
        layout.addWidget(self.cand_table, 2)

        crow = QHBoxLayout()
        self.btn_cand_ref = QPushButton("Copy reference for selected candidate")
        self.btn_cand_ref.clicked.connect(self._copy_candidate_reference)
        crow.addWidget(self.btn_cand_ref)
        crow.addStretch(1)
        layout.addLayout(crow)
        self.tabs.addTab(page, "Cite Assist")

    def _build_refs_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        info = QLabel(
            "Bibliography entries found in your document. Validation queries Crossref "
            "and OpenAlex (only the reference text is sent); DOI correctness and "
            "retraction status are checked on demand."
        )
        info.setObjectName("Muted")
        info.setWordWrap(True)
        layout.addWidget(info)
        self.ref_table = QTableWidget(0, 3)
        self.ref_table.setHorizontalHeaderLabels(["Reference", "Status", "Matched title"])
        rheader = self.ref_table.horizontalHeader()
        rheader.setSectionResizeMode(0, QHeaderView.Stretch)
        rheader.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        rheader.setSectionResizeMode(2, QHeaderView.Stretch)
        self.ref_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ref_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ref_table.setAlternatingRowColors(True)
        self.ref_table.itemDoubleClicked.connect(self._open_reference)
        layout.addWidget(self.ref_table, 1)
        rrow = QHBoxLayout()
        self.btn_validate_refs = QPushButton("Validate references (network)")
        self.btn_validate_refs.clicked.connect(self._validate_refs)
        self.ref_info = QLabel("")
        self.ref_info.setObjectName("Muted")
        rrow.addWidget(self.btn_validate_refs)
        rrow.addWidget(self.ref_info, 1)
        layout.addLayout(rrow)
        self.tabs.addTab(page, "References")

    def _build_cert_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.cert_info = QTextBrowser()
        self.cert_info.setPlaceholderText(
            "Run a scan to generate a certificate with report ID, hash and scores."
        )
        layout.addWidget(self.cert_info, 1)
        row = QHBoxLayout()
        self.btn_report = QPushButton("Export full report (PDF)")
        self.btn_report.setEnabled(False)
        self.btn_report.clicked.connect(self._export_report)
        self.btn_cert = QPushButton("Export certificate (PDF)")
        self.btn_cert.setObjectName("Primary")
        self.btn_cert.setEnabled(False)
        self.btn_cert.clicked.connect(self._export_certificate)
        self.btn_verify = QPushButton("Verify report ID")
        self.btn_verify.setEnabled(False)
        self.btn_verify.clicked.connect(self._verify_report)
        row.addWidget(self.btn_report)
        row.addWidget(self.btn_cert)
        row.addWidget(self.btn_verify)
        row.addStretch(1)
        layout.addLayout(row)
        self.tabs.addTab(page, "Certificate")

    def _build_history_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.history_table = QTableWidget(0, 6)
        self.history_table.setHorizontalHeaderLabels(
            ["Date", "Document", "Report ID", "Similarity %", "Integrity %", "Flags"]
        )
        header = self.history_table.horizontalHeader()
        for index in range(6):
            header.setSectionResizeMode(
                index, QHeaderView.Stretch if index == 1 else QHeaderView.ResizeToContents
            )
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table, 1)
        refresh = QPushButton("Refresh history")
        refresh.clicked.connect(self._refresh_history)
        layout.addWidget(refresh, alignment=Qt.AlignLeft)
        self.tabs.addTab(page, "History")

    # ============================================================ actions ==
    def _select_file(self, path: str) -> None:
        self.current_file = path
        self.drop_zone.set_file(path)
        self.status_lbl.setText(f"Selected: {Path(path).name}")

    def _choose_archive_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose archive folder")
        if folder:
            self.settings["archive_folder"] = folder
            try:
                save_settings(self.settings)
            except OSError:
                pass
            self._refresh_archive_label()

    def _refresh_archive_label(self) -> None:
        folder = str(self.settings.get("archive_folder", "") or "")
        if folder:
            self.archive_lbl.setText(Path(folder).name or folder)
            self.archive_lbl.setToolTip(folder)
        else:
            self.archive_lbl.setText("no folder selected")
            self.archive_lbl.setToolTip("")

    def _sync_settings(self) -> None:
        self.settings["enable_web"] = self.chk_web.isChecked()
        self.settings["enable_academic"] = self.chk_academic.isChecked()
        self.settings["enable_ai"] = self.chk_ai.isChecked()
        self.settings["exclude_quotes"] = self.chk_quotes.isChecked()
        self.settings["enable_archive"] = self.chk_archive.isChecked()
        self.settings["max_queries"] = self.spin_queries.value()
        try:
            save_settings(self.settings)
        except OSError:
            pass

    def _start_scan(self) -> None:
        if not self.current_file:
            QMessageBox.information(
                self, APP_NAME, "Drop a document first, or click the drop area to browse."
            )
            return
        if self.worker is not None and self.worker.isRunning():
            return
        if self.watch_worker is not None and self.watch_worker.isRunning():
            QMessageBox.information(self, APP_NAME, "A watched-folder scan is running.")
            return

        self._sync_settings()
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress.setValue(0)
        self.status_lbl.setText("Starting scan...")

        self.worker = ScanWorker(self.current_file, dict(self.settings), self)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _cancel_scan(self) -> None:
        cancelled = False
        for worker in (self.worker, self.batch_worker, self.func_worker):
            if worker is not None and worker.isRunning():
                worker.cancel()
                cancelled = True
        if cancelled:
            self.cancel_btn.setEnabled(False)
            self.status_lbl.setText("Cancelling...")

    def _on_progress(self, pct: int, message: str) -> None:
        self.progress.setValue(pct)
        self.status_lbl.setText(f"{message} ({pct}%)")

    def _on_failed(self, message: str) -> None:
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress.setValue(0)
        self.status_lbl.setText("Scan failed.")
        QMessageBox.warning(self, APP_NAME, f"Scan failed:\n{message}")

    def _on_done(self, result) -> None:
        self.result = result
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress.setValue(100)
        self.status_lbl.setText(
            f"Done: {len(result.matches)} flagged passage(s), "
            f"{len(result.sources)} source(s) checked."
        )
        try:
            db.save_scan(result)
        except Exception:
            pass
        self._populate(result)
        self._refresh_history()
        self.tabs.setCurrentIndex(0)

    # ====================================================== batch / watch ==
    def _start_batch(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose folder with documents")
        if folder:
            self._batch_from_folder(folder)

    def _batch_from_folder(self, folder: str) -> None:
        files = batch_mod.collect_documents(folder)
        if not files:
            QMessageBox.information(
                self, APP_NAME, "No supported documents (.docx, .pdf, .txt, .md, .rtf, .odt) found."
            )
            return
        out = QFileDialog.getExistingDirectory(
            self, "Choose output folder for reports", str(Path.home())
        )
        if not out:
            return
        self._sync_settings()
        self._batch_out = out
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_lbl.setText(f"Batch scanning {len(files)} document(s)...")
        self.batch_worker = BatchWorker([str(p) for p in files], dict(self.settings), out, self)
        self.batch_worker.progress.connect(self._on_progress)
        self.batch_worker.done.connect(self._on_batch_done)
        self.batch_worker.failed.connect(self._on_batch_failed)
        self.batch_worker.start()

    def _on_batch_done(self, results) -> None:
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        ok = [r for r in results if not isinstance(r, tuple)]
        errors = [r for r in results if isinstance(r, tuple)]
        self.status_lbl.setText(
            f"Batch done: {len(ok)} scanned, {len(errors)} failed. Reports in {self._batch_out}"
        )
        self._refresh_history()
        QMessageBox.information(
            self,
            APP_NAME,
            f"Batch finished.\n\nScanned: {len(ok)}\nFailed: {len(errors)}\n\n"
            f"Reports written to:\n{self._batch_out}\n\nOpen index.html for the overview.",
        )
        QDesktopServices.openUrl(QUrl.fromLocalFile(self._batch_out))

    def _on_batch_failed(self, message: str) -> None:
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        QMessageBox.warning(self, APP_NAME, f"Batch scan failed:\n{message}")

    def _init_watch(self) -> None:
        self.tray = QSystemTrayIcon(self._tray_icon(), self)
        self.tray.setToolTip(APP_NAME)
        self.watch_timer = QTimer(self)
        self.watch_timer.setInterval(4000)
        self.watch_timer.timeout.connect(self._watch_tick)
        if self.chk_watch.isChecked() and self.settings.get("watch_folder"):
            self._prime_watch()
            self.watch_timer.start()
            self.tray.show()

    def _tray_icon(self) -> QIcon:
        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(ACCENT))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 2, 60, 60, 16, 16)
        painter.setPen(QColor("#FFFFFF"))
        font = painter.font()
        font.setPointSize(30)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pix.rect(), Qt.AlignCenter, "A")
        painter.end()
        return QIcon(pix)

    def _choose_watch_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose folder to watch")
        if folder:
            self.settings["watch_folder"] = folder
            try:
                save_settings(self.settings)
            except OSError:
                pass
            self._refresh_watch_label()
            if self.chk_watch.isChecked():
                self._prime_watch()

    def _refresh_watch_label(self) -> None:
        folder = str(self.settings.get("watch_folder", "") or "")
        self.watch_lbl.setText(Path(folder).name if folder else "no folder selected")
        self.watch_lbl.setToolTip(folder)

    def _toggle_watch(self, checked: bool) -> None:
        self.settings["watch_enabled"] = bool(checked)
        try:
            save_settings(self.settings)
        except OSError:
            pass
        if checked:
            if not self.settings.get("watch_folder"):
                QMessageBox.information(
                    self, APP_NAME, "Choose a watch folder first (Folder... button)."
                )
                self.chk_watch.setChecked(False)
                return
            self._prime_watch()
            self.watch_timer.start()
            self.tray.show()
            self.status_lbl.setText(
                f"Watching {self.settings['watch_folder']} - new documents are scanned automatically."
            )
        else:
            self.watch_timer.stop()
            self.tray.hide()
            self.status_lbl.setText("Watch folder disabled.")

    def _prime_watch(self) -> None:
        self._watch_seen = {}
        folder = Path(str(self.settings.get("watch_folder", "") or ""))
        if folder.is_dir():
            for p in folder.iterdir():
                if p.is_file() and p.suffix.lower() in batch_mod.SUPPORTED:
                    try:
                        self._watch_seen[str(p)] = p.stat().st_mtime
                    except OSError:
                        pass

    def _watch_tick(self) -> None:
        folder = Path(str(self.settings.get("watch_folder", "") or ""))
        if not folder.is_dir():
            return
        try:
            entries = list(folder.iterdir())
        except OSError:
            return
        for p in entries:
            if not p.is_file() or p.suffix.lower() not in batch_mod.SUPPORTED:
                continue
            if p.name.startswith("~$"):
                continue
            key = str(p)
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            if self._watch_seen.get(key) != mtime:
                self._watch_seen[key] = mtime
                if key not in self._watch_queue:
                    self._watch_queue.append(key)
        self._start_next_watch()

    def _start_next_watch(self) -> None:
        if not self._watch_queue:
            return
        if (self.watch_worker is not None and self.watch_worker.isRunning()) or (
            self.worker is not None and self.worker.isRunning()
        ):
            return
        path = self._watch_queue.pop(0)
        self._sync_settings()
        self.status_lbl.setText(f"[watch] Scanning {Path(path).name}...")
        self.watch_worker = ScanWorker(path, dict(self.settings), self)
        self.watch_worker.progress.connect(self._on_progress)
        self.watch_worker.done.connect(self._on_watch_done)
        self.watch_worker.failed.connect(self._on_watch_failed)
        self.watch_worker.start()

    def _on_watch_done(self, result) -> None:
        try:
            db.save_scan(result)
        except Exception:
            pass
        out = Path(self._watch_out)
        try:
            out.mkdir(parents=True, exist_ok=True)
            findings.build_findings_html(
                result, str(out / f"{Path(result.file_path).stem}_{result.report_id}.html")
            )
        except Exception:
            pass
        message = (
            f"{result.file_name}: Similarity {result.similarity}%, "
            f"Integrity {result.integrity}%, {len(result.matches)} flag(s)."
        )
        self.status_lbl.setText(f"[watch] {message}")
        try:
            if self.tray.isVisible():
                self.tray.showMessage(APP_NAME, message + " Findings saved.", QSystemTrayIcon.Information, 6000)
        except Exception:
            pass
        self._refresh_history()
        self._start_next_watch()

    def _on_watch_failed(self, message: str) -> None:
        self.status_lbl.setText(f"[watch] Failed: {message}")
        self._start_next_watch()

    # ========================================================== populate ==
    def _populate(self, r) -> None:
        self.ring_sim.set_value(r.similarity)
        self.ring_para.set_value(r.paraphrase_risk)
        self.ring_ai.set_value(r.ai_likelihood)
        self.ring_int.set_value(r.integrity)

        dup_count = sum(1 for m in r.matches if m.match_type == "duplicate")
        gaps = getattr(r, "citation_gaps", []) or []
        refs = getattr(r, "ref_entries", []) or []

        warning_items = "".join(f"<li>{h(w)}</li>" for w in r.warnings) or "<li>None</li>"
        source_items = ""
        for source in r.sources[:8]:
            source_items += (
                f"<li>{h(source.title[:95])} \u2014 <b>{source.pct:.1f}%</b> "
                f"<span style='color:#8A94A6'>({h(source.kind)})</span></li>"
            )
        if not source_items:
            source_items = "<li>No sources matched within this scan's coverage.</li>"
        ai_note = h(r.ai_details.get("note", "")) if r.ai_details else ""
        ai_version = h(r.ai_details.get("version", "")) if r.ai_details else ""
        flagged = (r.ai_details or {}).get("flagged", [])
        flagged_items = "".join(f"<li>{h(s)}</li>" for s in flagged)
        flagged_block = (
            f"<h4 style='margin:12px 0 4px 0;'>AI-suspicious sentences</h4>"
            f"<ul>{flagged_items}</ul>"
            if flagged_items
            else ""
        )

        self.summary_info.setHtml(
            f"""
            <div style="color:#E8EDF4;">
              <h3 style="margin:2px 0;">{h(r.file_name)}</h3>
              <p style="color:#8A94A6; margin:2px 0;">
                {r.words:,} words &middot; {r.pages} page(s) &middot;
                {r.content_tokens:,} content tokens &middot; {r.queries_run} queries &middot;
                {len(r.sources)} sources &middot; {len(r.matches)} flags
                ({dup_count} internal dup)
              </p>
              <p style="color:#8A94A6; margin:2px 0;">
                {len(gaps)} citation gap(s) &middot; {len(refs)} reference(s) parsed &middot;
                Strictness: <b>{h(getattr(r, "strictness", "balanced"))}</b> &middot;
                Report ID: <b>{h(r.report_id)}</b> &middot;
                SHA-256: {h(r.doc_hash[:24])}&hellip;
              </p>
              <h4 style="margin:12px 0 4px 0;">Top sources</h4>
              <ul>{source_items}</ul>
              <h4 style="margin:12px 0 4px 0;">Coverage notes</h4>
              <ul>{warning_items}</ul>
              {flagged_block}
              {"<p style='color:#8A94A6;'>AI analysis: " + ai_note + "</p>" if ai_note else ""}
            </div>
            """
        )

        # matches tab
        self._result_matches = list(r.matches)
        self.matches_table.setRowCount(len(r.matches))
        for row, match in enumerate(r.matches):
            label = MATCH_LABELS.get(match.match_type, match.match_type)
            cells = [label, str(match.tokens), match.source_title[:90], match.text[:220]]
            for col, text in enumerate(cells):
                self.matches_table.setItem(row, col, QTableWidgetItem(text))
            color = QColor(MATCH_COLORS.get(match.match_type, "#8A94A6"))
            type_item = self.matches_table.item(row, 0)
            if type_item is not None:
                type_item.setForeground(QBrush(color))
                font = type_item.font()
                font.setBold(True)
                type_item.setFont(font)
            for col in range(4):
                item = self.matches_table.item(row, col)
                if item is not None:
                    bg = QColor(color)
                    bg.setAlpha(36 if col == 0 else 14)
                    item.setBackground(QBrush(bg))

        # fix & cite tab
        self.fix_table.setRowCount(len(r.matches))
        for row, match in enumerate(r.matches):
            label = MATCH_LABELS.get(match.match_type, match.match_type)
            cells = [label, match.source_title[:70], match.text[:150], match.suggestion[:150]]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col == 3:
                    item.setToolTip(match.suggestion)
                self.fix_table.setItem(row, col, item)
            color = QColor(MATCH_COLORS.get(match.match_type, "#8A94A6"))
            type_item = self.fix_table.item(row, 0)
            if type_item is not None:
                type_item.setForeground(QBrush(color))
                font = type_item.font()
                font.setBold(True)
                type_item.setFont(font)
            for col in range(4):
                item = self.fix_table.item(row, col)
                if item is not None:
                    bg = QColor(color)
                    bg.setAlpha(36 if col == 0 else 12)
                    item.setBackground(QBrush(bg))

        # cite assist tab
        self._gaps = list(gaps)
        self.gap_table.setRowCount(len(gaps))
        for row, gap in enumerate(gaps):
            self.gap_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.gap_table.setItem(row, 1, QTableWidgetItem(gap.get("reason", "")))
            self.gap_table.setItem(row, 2, QTableWidgetItem(gap.get("text", "")[:300]))
        self._candidates = []
        self.cand_table.setRowCount(0)

        # references tab
        self._ref_results = []
        self.ref_table.setRowCount(len(refs))
        for row, entry in enumerate(refs):
            self.ref_table.setItem(row, 0, QTableWidgetItem(entry[:200]))
            self.ref_table.setItem(row, 1, QTableWidgetItem("Not validated"))
            self.ref_table.setItem(row, 2, QTableWidgetItem(""))
        self.ref_info.setText(f"{len(refs)} entr{'y' if len(refs) == 1 else 'ies'} parsed.")

        # certificate tab
        license_text = "Registered copy" if r.licensed else "Unregistered copy (trial watermark)"
        self.cert_info.setHtml(
            f"""
            <div style="color:#E8EDF4;">
              <h3 style="margin:2px 0;">Certificate details</h3>
              <p>Report ID: <b>{h(r.report_id)}</b><br/>
                 Generated: {h(r.timestamp)}<br/>
                 Document: {h(r.file_name)}<br/>
                 SHA-256: {h(r.doc_hash)}<br/>
                 License status: {license_text}<br/>
                 Stylometry: {ai_version or "n/a"}</p>
              <p style="color:#8A94A6;">
                The certificate PDF carries these scores, the document hash, a QR code
                and the report ID. Both exports are standard PDF files you can print
                or attach to a submission package.
              </p>
            </div>
            """
        )
        self.btn_report.setEnabled(True)
        self.btn_cert.setEnabled(True)
        self.btn_verify.setEnabled(True)
        self.btn_findings.setEnabled(True)
        self.btn_highlight.setEnabled(bool(r.full_text))
        self.btn_word.setEnabled(Path(r.file_path).suffix.lower() == ".docx")
        self.btn_worklist.setEnabled(bool(r.matches))

    def _show_match_detail(self) -> None:
        row = self.matches_table.currentRow()
        if row < 0 or row >= len(self._result_matches):
            return
        match = self._result_matches[row]
        snippet = (
            f"<div style='background:#10161F; padding:10px; border-radius:6px;'>{h(match.source_snippet)}</div>"
            if match.source_snippet
            else "<p style='color:#8A94A6;'>(no source context captured)</p>"
        )
        source_line = (
            f"<a style='color:#5B8CFF;' href='{h(match.source_url)}'>{h(match.source_url)}</a>"
            if match.source_url
            else "<span style='color:#8A94A6;'>internal comparison</span>"
        )
        color = MATCH_COLORS.get(match.match_type, "#8A94A6")
        label = MATCH_LABELS.get(match.match_type, match.match_type)
        self.match_detail.setHtml(
            f"""
            <div style="color:#E8EDF4;">
              <p><span style="background:{color}33; color:{color}; padding:2px 10px;
                 border-radius:10px; font-weight:700;">{h(label)}</span>
                 &middot; {match.tokens} tokens &middot; weight {match.weight}</p>
              <table width="100%" cellspacing="8"><tr>
                <td width="50%" valign="top">
                  <div style="color:#8A94A6;">YOUR DOCUMENT</div>
                  <div style="background:#10161F; border-left:3px solid {color}; padding:10px; border-radius:6px;">{h(match.text)}</div>
                </td>
                <td width="50%" valign="top">
                  <div style="color:#8A94A6;">SOURCE PASSAGE</div>
                  {snippet}
                </td>
              </tr></table>
              <p style="color:#8A94A6;">Source: {h(match.source_title)} &middot; {source_line}</p>
              <p style="color:#8A94A6;"><i>{h(match.suggestion)}</i></p>
            </div>
            """
        )

    # ================================================== cite assist flow ==
    def _run_func(self, func, on_done, busy_message: str) -> None:
        if self.func_worker is not None and self.func_worker.isRunning():
            QMessageBox.information(self, APP_NAME, "Another background task is running.")
            return
        self.status_lbl.setText(busy_message)
        self.cancel_btn.setEnabled(True)
        self.func_worker = FuncWorker(func, self)

        def _progress(pct, msg):
            self.progress.setValue(pct)
            self.status_lbl.setText(msg)

        def _done(payload):
            self.cancel_btn.setEnabled(False)
            self.progress.setValue(0)
            on_done(payload)

        def _failed(message):
            self.cancel_btn.setEnabled(False)
            self.progress.setValue(0)
            QMessageBox.warning(self, APP_NAME, f"Task failed:\n{message}")

        self.func_worker.progress.connect(_progress)
        self.func_worker.done.connect(_done)
        self.func_worker.failed.connect(_failed)
        self.func_worker.start()

    def _find_sources_selected(self) -> None:
        row = self.gap_table.currentRow()
        if row < 0 or row >= len(self._gaps):
            QMessageBox.information(self, APP_NAME, "Select a citation gap first.")
            return
        gap_row, sentence = row, self._gaps[row]["text"]
        settings = dict(self.settings)

        def job(progress=None, cancel=None):
            from ..core.citation import suggest_for_sentence

            hits = suggest_for_sentence(sentence, settings)
            return (gap_row, sentence, hits)

        self._run_func(job, self._on_candidates_done, "Searching academic databases...")

    def _find_top_gaps(self) -> None:
        if not self._gaps:
            QMessageBox.information(self, APP_NAME, "No citation gaps in this scan.")
            return
        top = list(enumerate(self._gaps[:3]))
        settings = dict(self.settings)

        def job(progress=None, cancel=None):
            from ..core.citation import suggest_for_sentence

            collected = []
            total = max(len(top), 1)
            for i, (gap_row, gap) in enumerate(top):
                if cancel and cancel():
                    break
                if progress:
                    progress(int(100 * i / total), f"Searching sources for gap {i + 1}/{total}...")
                collected.append((gap_row, gap["text"], suggest_for_sentence(gap["text"], settings)))
            return collected

        self._run_func(job, self._on_candidates_multi_done, "Searching top citation gaps...")

    def _on_candidates_done(self, payload) -> None:
        self._on_candidates_multi_done([payload])

    def _on_candidates_multi_done(self, payload) -> None:
        added = 0
        for gap_row, sentence, hits in payload:
            for hit in hits:
                self._candidates.append(
                    {"gap": gap_row, "sentence": sentence, "title": hit.get("title", ""),
                     "url": hit.get("url", ""), "doi": hit.get("doi", "")}
                )
                row = self.cand_table.rowCount()
                self.cand_table.insertRow(row)
                self.cand_table.setItem(row, 0, QTableWidgetItem(f"#{gap_row + 1}"))
                self.cand_table.setItem(row, 1, QTableWidgetItem(hit.get("title", "")[:160]))
                link = hit.get("doi") or hit.get("url", "")
                self.cand_table.setItem(row, 2, QTableWidgetItem(str(link)[:160]))
                added += 1
        self.status_lbl.setText(f"Added {added} candidate source(s). Double-click to open.")

    def _open_candidate(self) -> None:
        row = self.cand_table.currentRow()
        if row < 0 or row >= len(self._candidates):
            return
        url = self._candidates[row].get("url") or self._candidates[row].get("doi")
        if url:
            if not str(url).lower().startswith("http"):
                url = f"https://doi.org/{url}"
            QDesktopServices.openUrl(QUrl(str(url)))

    def _copy_candidate_reference(self) -> None:
        row = self.cand_table.currentRow()
        if row < 0 or row >= len(self._candidates):
            QMessageBox.information(self, APP_NAME, "Select a candidate first.")
            return
        item = self._candidates[row]
        reference = (
            f"{item['title']}. Retrieved from {item['url'] or item['doi']} "
            f"(accessed {__import__('datetime').date.today().strftime('%d %b %Y')})."
        )
        QApplication.clipboard().setText(reference)
        self.status_lbl.setText("Candidate reference copied to clipboard.")

    # ======================================================= references ==
    def _validate_refs(self) -> None:
        if not self.result or not getattr(self.result, "ref_entries", None):
            QMessageBox.information(
                self, APP_NAME,
                "No bibliography entries were found in this document's References section.",
            )
            return
        entries = list(self.result.ref_entries)
        timeout = int(self.settings.get("fetch_timeout", 12))

        def job(progress=None, cancel=None):
            from ..core.references import validate_entries

            return validate_entries(
                entries,
                timeout=timeout,
                progress=lambda i, total, msg: progress(
                    int(100 * i / max(total, 1)), f"Checking references {i}/{total}..."
                ),
                cancel=cancel,
            )

        self._run_func(job, self._on_refs_done, "Validating references (network)...")

    def _on_refs_done(self, results) -> None:
        self._ref_results = list(results)
        from ..core.references import STATUS_LABELS

        bad = 0
        for row, result in enumerate(results):
            if row >= self.ref_table.rowCount():
                break
            status = result.get("status", "")
            if status in ("doi_not_found", "doi_mismatch", "retracted", "not_found"):
                bad += 1
            self.ref_table.setItem(row, 1, QTableWidgetItem(STATUS_LABELS.get(status, status)))
            self.ref_table.setItem(row, 2, QTableWidgetItem(result.get("matched", "")[:160]))
            color = None
            if status in ("retracted", "doi_not_found", "doi_mismatch"):
                color = "#FF5B5B"
            elif status == "not_found":
                color = "#FF9F40"
            elif status in ("verified", "verified_no_doi"):
                color = "#34D399"
            if color:
                for col in range(3):
                    it = self.ref_table.item(row, col)
                    if it is not None:
                        it.setForeground(QColor(color))
        self.ref_info.setText(f"Validated {len(results)}; {bad} need attention. Double-click a row to open.")

    def _open_reference(self) -> None:
        row = self.ref_table.currentRow()
        if row < 0 or row >= len(self._ref_results):
            return
        url = self._ref_results[row].get("url", "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    # =========================================================== exports ==
    def _export_report(self) -> None:
        if not self.result:
            return
        default = str(Path.home() / f"Attribo_Report_{self.result.report_id}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Save report", default, "PDF (*.pdf)")
        if not path:
            return
        try:
            pdf_builder.build_report(self.result, path)
            QMessageBox.information(self, APP_NAME, f"Report saved:\n{path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Could not write PDF:\n{exc}")

    def _export_certificate(self) -> None:
        if not self.result:
            return
        default = str(Path.home() / f"Attribo_Certificate_{self.result.report_id}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Save certificate", default, "PDF (*.pdf)")
        if not path:
            return
        try:
            pdf_builder.build_certificate(self.result, path, licensed=self.result.licensed)
            QMessageBox.information(self, APP_NAME, f"Certificate saved:\n{path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Could not write PDF:\n{exc}")

    def _export_findings(self) -> None:
        if not self.result:
            QMessageBox.information(self, APP_NAME, "Run a scan first.")
            return
        default = str(Path.home() / f"Attribo_Findings_{self.result.report_id}.html")
        path, _ = QFileDialog.getSaveFileName(self, "Save findings", default, "HTML (*.html)")
        if not path:
            return
        try:
            findings.build_findings_html(self.result, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Could not write findings:\n{exc}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        self.status_lbl.setText(f"Findings saved and opened: {path}")

    def _export_highlight(self) -> None:
        if not self.result or not self.result.full_text:
            QMessageBox.information(self, APP_NAME, "Run a scan first.")
            return
        default = str(Path.home() / f"Attribo_Highlighted_{self.result.report_id}.html")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save highlighted copy", default, "HTML (*.html)"
        )
        if not path:
            return
        try:
            highlight.build_highlight_html(self.result, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Could not write highlighted copy:\n{exc}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        self.status_lbl.setText(f"Highlighted copy saved and opened: {path}")

    def _export_word(self) -> None:
        if not self.result:
            QMessageBox.information(self, APP_NAME, "Run a scan first.")
            return
        if Path(self.result.file_path).suffix.lower() != ".docx":
            QMessageBox.information(
                self, APP_NAME,
                "Word comment export works for .docx documents. For PDFs, use the "
                "highlighted HTML copy instead.",
            )
            return
        default = str(Path.home() / f"Attribo_Review_{self.result.report_id}.docx")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Word review copy", default, "Word document (*.docx)"
        )
        if not path:
            return
        try:
            added, skipped = word_export.export_docx_with_comments(self.result, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Could not write Word copy:\n{exc}")
            return
        QMessageBox.information(
            self,
            APP_NAME,
            f"Word review copy saved:\n{path}\n\n"
            f"{added} comment(s) inserted, {skipped} flag(s) could not be located.",
        )
        self.status_lbl.setText(f"Word review copy saved: {path}")

    def _copy_fix(self) -> None:
        row = self.fix_table.currentRow()
        if row < 0 or row >= len(self._result_matches):
            QMessageBox.information(
                self, APP_NAME, "Select a row in the Fix & Cite table first."
            )
            return
        try:
            text = fixcite.copy_block(self._result_matches[row])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Could not build the fix text:\n{exc}")
            return
        QApplication.clipboard().setText(text)
        self.status_lbl.setText("Fix copied to clipboard - paste into your draft or notes.")

    def _export_worklist(self) -> None:
        if not self.result or not self.result.matches:
            QMessageBox.information(
                self, APP_NAME, "Run a scan first - the worklist needs at least one flag."
            )
            return
        default = str(Path.home() / f"Attribo_Worklist_{self.result.report_id}.docx")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Fix & Cite worklist", default, "Word document (*.docx)"
        )
        if not path:
            return
        try:
            count = word_export.build_worklist_docx(self.result, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Could not write worklist:\n{exc}")
            return
        QMessageBox.information(
            self,
            APP_NAME,
            f"Fix & Cite worklist saved:\n{path}\n\n"
            f"{count} flag(s) with read-and-replace rows.",
        )
        self.status_lbl.setText(f"Worklist saved: {path}")

    def _verify_report(self) -> None:
        if not self.result:
            return
        try:
            rows = db.recent_scans(500)
        except Exception:
            rows = []
        found = any(str(row[2]) == self.result.report_id for row in rows)
        if found:
            QMessageBox.information(
                self,
                APP_NAME,
                f"Report ID {self.result.report_id} is present in this PC's scan history.",
            )
        else:
            QMessageBox.warning(
                self,
                APP_NAME,
                f"Report ID {self.result.report_id} was not found in this PC's scan history.",
            )

    # ======================================================== fix & cite ==
    def _selected_fix_match(self):
        row = self.fix_table.currentRow()
        if row < 0 or row >= len(self._result_matches):
            return None
        return self._result_matches[row]

    def _copy_reference(self) -> None:
        match = self._selected_fix_match()
        if match is None:
            QMessageBox.information(
                self, APP_NAME, "Select a row in the Fix & Cite table first."
            )
            return
        reference = (
            f"{match.source_title}. Retrieved from {match.source_url} "
            f"(accessed {__import__('datetime').date.today().strftime('%d %b %Y')})."
        )
        QApplication.clipboard().setText(reference)
        self.status_lbl.setText("Reference copied to clipboard.")

    def _open_source(self) -> None:
        match = self._selected_fix_match()
        if match is None:
            QMessageBox.information(
                self, APP_NAME, "Select a row in the Fix & Cite table first."
            )
            return
        if match.source_url:
            QDesktopServices.openUrl(QUrl(match.source_url))

    # =========================================================== settings ==
    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings.update(dialog.values())
            try:
                save_settings(self.settings)
            except OSError:
                pass
            self.chk_web.setChecked(bool(self.settings.get("enable_web", True)))
            self.chk_academic.setChecked(bool(self.settings.get("enable_academic", True)))
            self.chk_ai.setChecked(bool(self.settings.get("enable_ai", True)))
            self.chk_quotes.setChecked(bool(self.settings.get("exclude_quotes", False)))
            self._refresh_archive_label()
            self._refresh_license_label()

    def _refresh_license_label(self) -> None:
        info = verify_key(str(self.settings.get("license_key", "")))
        if info and not info.get("expired"):
            self.license_lbl.setText(f"Licensed to {info['name']}")
        elif info and info.get("expired"):
            self.license_lbl.setText("License expired")
        else:
            self.license_lbl.setText("Unregistered copy")

    # =========================================================== updates ==
    def _init_updates(self) -> None:
        if not self.settings.get("auto_update_check", True):
            return
        QTimer.singleShot(3000, lambda: self._check_updates(auto=True))

    def _check_updates(self, auto: bool = False) -> None:
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        self._update_worker = FuncWorker(
            lambda progress=None, cancel=None: updater.check_for_update(), self
        )

        def _done(info):
            self._update_info = info
            if info.get("update_available"):
                self._show_update_banner(info)
                if self.settings.get("auto_update_download", False) and info.get("download_url"):
                    self.status_lbl.setText(
                        f"Update v{info['latest']} found - downloading in the background..."
                    )
                    self._download_update()
            elif not auto:
                if info.get("latest"):
                    QMessageBox.information(
                        self,
                        APP_NAME,
                        f"You are on the latest version (v{info.get('current', __version__)}).",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        APP_NAME,
                        "Could not read the update channel. Check your connection - if you "
                        "are online, the GitHub repository may be private or not yet "
                        "published.",
                    )

        def _failed(message):
            if not auto:
                QMessageBox.warning(self, APP_NAME, f"Update check failed:\n{message}")

        self._update_worker.done.connect(_done)
        self._update_worker.failed.connect(_failed)
        self._update_worker.start()

    def _show_update_banner(self, info) -> None:
        self.update_btn.setText(f"Update v{info['latest']} available")
        self.update_btn.setToolTip(
            f"Click to install v{info['latest']} (you have v{info['current']})."
        )
        self.update_btn.setVisible(True)
        try:
            if self.tray.isVisible():
                self.tray.showMessage(
                    APP_NAME,
                    f"Update v{info['latest']} is available.",
                    QSystemTrayIcon.Information,
                    6000,
                )
        except Exception:
            pass

    def _show_update_dialog(self) -> None:
        info = self._update_info or {}
        if not info.get("latest"):
            self._check_updates(auto=False)
            return
        box = QMessageBox(self)
        box.setWindowTitle("Attribo update")
        box.setIcon(QMessageBox.Information)
        box.setText(f"v{info['latest']} is available (you have v{info['current']}).")
        notes = (info.get("notes") or "").strip()
        box.setInformativeText(notes[:1200] or "Open the releases page for details.")
        install_btn = (
            box.addButton("Download && install", QMessageBox.AcceptRole)
            if info.get("download_url")
            else None
        )
        open_btn = box.addButton("Open releases page", QMessageBox.ActionRole)
        box.addButton("Later", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if install_btn is not None and clicked is install_btn:
            self._download_update()
        elif clicked is open_btn:
            QDesktopServices.openUrl(QUrl(info.get("html_url") or updater.RELEASES_PAGE))

    def _download_update(self) -> None:
        info = self._update_info or {}
        url = info.get("download_url", "")
        if not url:
            QDesktopServices.openUrl(QUrl(info.get("html_url") or updater.RELEASES_PAGE))
            return
        if self.func_worker is not None and self.func_worker.isRunning():
            return

        def job(progress=None, cancel=None):
            return updater.download_installer(
                url, progress=lambda frac, msg: progress(int(frac * 100), msg)
            )

        self.func_worker = FuncWorker(job, self)

        def _prog(pct, msg):
            self.progress.setValue(pct)
            self.status_lbl.setText(msg)

        def _done(path):
            self._downloaded_update = path
            self.progress.setValue(0)
            self.status_lbl.setText("Update downloaded.")
            answer = QMessageBox.question(
                self,
                APP_NAME,
                f"Update downloaded to:\n{path}\n\nClose {APP_NAME} and install now?",
            )
            if answer == QMessageBox.Yes:
                try:
                    updater.launch_installer(path)
                except Exception as exc:  # noqa: BLE001
                    QMessageBox.warning(
                        self, APP_NAME, f"Could not start the installer:\n{exc}"
                    )
                    return
                QApplication.quit()

        def _failed(message):
            self.progress.setValue(0)
            QMessageBox.warning(self, APP_NAME, f"Update download failed:\n{message}")

        self.func_worker.progress.connect(_prog)
        self.func_worker.done.connect(_done)
        self.func_worker.failed.connect(_failed)
        self.func_worker.start()

    def _refresh_history(self) -> None:
        try:
            rows = db.recent_scans(50)
        except Exception:
            rows = []
        self.history_table.setRowCount(len(rows))
        for r_i, row in enumerate(rows):
            for c_i, value in enumerate(row):
                self.history_table.setItem(r_i, c_i, QTableWidgetItem(str(value)))

    # ======================================================= drag & drop ==
    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                if Path(path).is_dir():
                    self._batch_from_folder(path)
                else:
                    self._select_file(path)
                event.acceptProposedAction()
