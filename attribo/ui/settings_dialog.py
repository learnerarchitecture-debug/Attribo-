"""
Settings dialog: API keys, scanning thresholds, AI/semantic options, license.

Tabbed layout keeps the dialog compact so it fits laptop screens; the size is
additionally clamped to the available screen area.

(c) 2026 Attribo. All rights reserved.
"""
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .func_worker import FuncWorker
from .. import __version__
from ..core import semantic, strictness, updater
from ..licensing.keycheck import verify_key


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings — Attribo")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_search_tab(settings)
        self._build_scanning_tab(settings)
        self._build_ai_tab(settings)
        self._build_license_tab(settings)
        self._build_updates_tab(settings)

        hint = QLabel(
            "Keys are stored locally in %APPDATA%\\Attribo. "
            "All supported providers have card-free free tiers — see docs/API_KEYS.md."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Fit to the available screen area (never taller/wider than the display)
        screen = QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            self.setMaximumWidth(int(avail.width() * 0.95))
            self.setMaximumHeight(int(avail.height() * 0.90))
            self.resize(
                min(680, int(avail.width() * 0.9)), min(560, int(avail.height() * 0.85))
            )

        self.license.textChanged.connect(self._check_license)
        self._check_license()

    # ------------------------------------------------------------------ tabs
    def _build_search_tab(self, settings: dict) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        form = QFormLayout()
        form.setSpacing(8)

        self.google_key = QLineEdit(str(settings.get("google_api_key", "")))
        self.google_key.setPlaceholderText("Google Custom Search API key")
        self.google_cx = QLineEdit(str(settings.get("google_cx", "")))
        self.google_cx.setPlaceholderText("Search engine ID (cx)")
        self.brave_key = QLineEdit(str(settings.get("brave_api_key", "")))
        self.brave_key.setPlaceholderText("Brave Search API key (no card)")
        self.serper_key = QLineEdit(str(settings.get("serper_api_key", "")))
        self.serper_key.setPlaceholderText("Serper.dev API key (free credits, no card)")
        self.tavily_key = QLineEdit(str(settings.get("tavily_api_key", "")))
        self.tavily_key.setPlaceholderText("Tavily API key (free tier, no card)")
        self.exa_key = QLineEdit(str(settings.get("exa_api_key", "")))
        self.exa_key.setPlaceholderText("Exa API key (free credits, no card)")
        self.searxng_url = QLineEdit(str(settings.get("searxng_url", "")))
        self.searxng_url.setPlaceholderText("http://localhost:8888 (your own SearXNG, optional)")

        self.cross_verify = QCheckBox(
            "Cross-check: query all configured providers and merge results"
        )
        self.cross_verify.setChecked(bool(settings.get("cross_verify_providers", True)))

        self._test_worker = None
        self.test_btn = QPushButton("Test search APIs")
        self.test_btn.clicked.connect(self._test_providers)
        self.test_status = QLabel("")
        self.test_status.setObjectName("Muted")
        self.test_status.setWordWrap(True)

        form.addRow("Google API key", self.google_key)
        form.addRow("Google search engine ID", self.google_cx)
        form.addRow("Brave API key", self.brave_key)
        form.addRow("Serper API key", self.serper_key)
        form.addRow("Tavily API key", self.tavily_key)
        form.addRow("Exa API key", self.exa_key)
        form.addRow("SearXNG URL", self.searxng_url)
        form.addRow("", self.cross_verify)
        form.addRow("", self.test_btn)
        form.addRow("", self.test_status)
        outer.addLayout(form)

        note = QLabel(
            "Every result is fetched and verified against the real page text, so any "
            "combination of providers is safe to mix."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        outer.addWidget(note)
        outer.addStretch(1)
        self.tabs.addTab(page, "Search APIs")

    def _build_scanning_tab(self, settings: dict) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        form = QFormLayout()
        form.setSpacing(8)

        self.min_words = QSpinBox()
        self.min_words.setRange(5, 20)
        self.min_words.setValue(int(settings.get("min_match_words", 8)))

        self.strictness = QComboBox()
        for level in strictness.LEVELS:
            self.strictness.addItem(strictness.LEVEL_LABELS[level], level)
        self.strictness.setCurrentIndex(
            max(0, self.strictness.findData(str(settings.get("strictness", "strict"))))
        )

        self.max_queries = QSpinBox()
        self.max_queries.setRange(2, 50)
        self.max_queries.setValue(int(settings.get("max_queries", 12)))

        self.enable_web = QCheckBox("Web checking (all configured providers)")
        self.enable_web.setChecked(bool(settings.get("enable_web", True)))
        self.enable_academic = QCheckBox("Academic checking (OpenAlex / Crossref)")
        self.enable_academic.setChecked(bool(settings.get("enable_academic", True)))
        self.enable_ai = QCheckBox("AI-likelihood analysis (local)")
        self.enable_ai.setChecked(bool(settings.get("enable_ai", True)))
        self.exclude_quotes = QCheckBox("Exclude quoted blocks from scoring")
        self.exclude_quotes.setChecked(bool(settings.get("exclude_quotes", False)))

        form.addRow("Scan strictness", self.strictness)
        form.addRow("Minimum match length (words)", self.min_words)
        form.addRow("Search queries per scan", self.max_queries)
        form.addRow("", self.enable_web)
        form.addRow("", self.enable_academic)
        form.addRow("", self.enable_ai)
        form.addRow("", self.exclude_quotes)
        outer.addLayout(form)
        strict_note = QLabel(
            "Strict (default) flags shorter overlaps, runs more queries, lowers the "
            "semantic threshold and raises paraphrase sensitivity. Maximum flags even "
            "small overlaps - expect more false positives; always review before acting."
        )
        strict_note.setObjectName("Muted")
        strict_note.setWordWrap(True)
        outer.addWidget(strict_note)
        outer.addStretch(1)
        self.tabs.addTab(page, "Scanning")

    def _build_ai_tab(self, settings: dict) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)

        self.enable_semantic = QCheckBox(
            "Semantic matching (AI embeddings, optional, runs offline)"
        )
        self.enable_semantic.setChecked(bool(settings.get("enable_semantic", False)))
        outer.addWidget(self.enable_semantic)

        self._sem_worker = None
        self.semantic_btn = QPushButton("Download semantic model (~90 MB)")
        self.semantic_btn.clicked.connect(self._download_semantic)
        outer.addWidget(self.semantic_btn)

        self.semantic_status = QLabel("")
        self.semantic_status.setObjectName("Muted")
        self.semantic_status.setWordWrap(True)
        self._refresh_semantic_status()
        outer.addWidget(self.semantic_status)

        note = QLabel(
            "One-time model download from Hugging Face, then 100% offline. Catches "
            "synonym-level paraphrase that stem and TF-IDF matching cannot see "
            "(threshold cosine \u2265 0.70)."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        outer.addWidget(note)
        outer.addStretch(1)
        self.tabs.addTab(page, "AI & Semantic")

    def _build_license_tab(self, settings: dict) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        form = QFormLayout()
        form.setSpacing(8)

        self.license = QLineEdit(str(settings.get("license_key", "")))
        self.license.setPlaceholderText("AI-NAME-YYYY-MM-DD-SIGNATURE")
        self.license_status = QLabel("")
        self.license_status.setObjectName("Muted")
        self.license_status.setWordWrap(True)

        form.addRow("License key", self.license)
        form.addRow("", self.license_status)
        outer.addLayout(form)

        note = QLabel(
            "Offline license keys are verified locally (HMAC) — no activation server, "
            "nothing sent. Unlicensed copies are fully functional but certificates are "
            "watermarked \u201cUnregistered copy\u201d."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        outer.addWidget(note)
        outer.addStretch(1)
        self.tabs.addTab(page, "License")

    def _build_updates_tab(self, settings: dict) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        form = QFormLayout()
        form.setSpacing(8)

        self.auto_update_check = QCheckBox("Check for updates on startup (GitHub, optional)")
        self.auto_update_check.setChecked(bool(settings.get("auto_update_check", True)))
        self.auto_update_download = QCheckBox(
            "Download updates automatically when one is found"
        )
        self.auto_update_download.setChecked(bool(settings.get("auto_update_download", False)))
        form.addRow("", self.auto_update_check)
        form.addRow("", self.auto_update_download)
        outer.addLayout(form)

        self._upd_worker = None
        row = QHBoxLayout()
        self.upd_btn = QPushButton("Check for updates now")
        self.upd_btn.clicked.connect(self._check_updates_now)
        self.upd_open = QPushButton("Open releases page")
        self.upd_open.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(updater.RELEASES_PAGE))
        )
        row.addWidget(self.upd_btn)
        row.addWidget(self.upd_open)
        row.addStretch(1)
        outer.addLayout(row)

        self.upd_status = QLabel(f"Current version: v{__version__}")
        self.upd_status.setObjectName("Muted")
        self.upd_status.setWordWrap(True)
        outer.addWidget(self.upd_status)

        note = QLabel(
            "The update check reads the public GitHub repository only - your documents "
            "are never uploaded, and the check fails silently when offline."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        outer.addWidget(note)
        outer.addStretch(1)
        self.tabs.addTab(page, "Updates")

    # ------------------------------------------------------------- semantic
    def _refresh_semantic_status(self) -> None:
        self.semantic_status.setText(semantic.status_text())

    def _download_semantic(self) -> None:
        if self._sem_worker is not None and self._sem_worker.isRunning():
            return
        self.semantic_btn.setEnabled(False)
        self.semantic_status.setText("Downloading model...")

        def job(progress=None, cancel=None):
            ok, message = semantic.download(
                progress=lambda frac, msg: progress(int(frac * 100), msg)
            )
            return ok, message

        self._sem_worker = FuncWorker(job, self)

        def _done(payload):
            _ok, message = payload
            self.semantic_status.setText(message)
            self.semantic_btn.setEnabled(True)
            self._refresh_semantic_status()

        def _failed(message):
            self.semantic_status.setText(f"Download failed: {message}")
            self.semantic_btn.setEnabled(True)

        self._sem_worker.done.connect(_done)
        self._sem_worker.failed.connect(_failed)
        self._sem_worker.start()

    # ---------------------------------------------------------------- tests
    def _test_providers(self) -> None:
        if self._test_worker is not None and self._test_worker.isRunning():
            return
        settings_like = {
            "google_api_key": self.google_key.text().strip(),
            "google_cx": self.google_cx.text().strip(),
            "brave_api_key": self.brave_key.text().strip(),
            "serper_api_key": self.serper_key.text().strip(),
            "tavily_api_key": self.tavily_key.text().strip(),
            "exa_api_key": self.exa_key.text().strip(),
            "searxng_url": self.searxng_url.text().strip(),
            "fetch_timeout": 15,
        }
        self.test_btn.setEnabled(False)
        self.test_status.setText("Testing configured providers...")

        def job(progress=None, cancel=None):
            from ..engines.web_engine import WebChecker

            return WebChecker(settings_like).probe(progress=progress)

        self._test_worker = FuncWorker(job, self)

        def _done(results):
            self.test_btn.setEnabled(True)
            if not results:
                self.test_status.setText("No search providers configured yet.")
                return
            lines = []
            for result in results:
                mark = "OK" if result["ok"] else "FAIL"
                lines.append(f"{result['provider']}: {mark} - {result['message']}")
            self.test_status.setText(" | ".join(lines))

        def _failed(message):
            self.test_btn.setEnabled(True)
            self.test_status.setText(f"Test failed: {message}")

        self._test_worker.done.connect(_done)
        self._test_worker.failed.connect(_failed)
        self._test_worker.start()

    # --------------------------------------------------------------- updates
    def _check_updates_now(self) -> None:
        if self._upd_worker is not None and self._upd_worker.isRunning():
            return
        self.upd_btn.setEnabled(False)
        self.upd_status.setText("Checking GitHub...")

        def job(progress=None, cancel=None):
            return updater.check_for_update()

        self._upd_worker = FuncWorker(job, self)

        def _done(info):
            self.upd_btn.setEnabled(True)
            if not info.get("latest"):
                self.upd_status.setText("Could not reach GitHub (offline?). Try again later.")
            elif info.get("update_available"):
                self.upd_status.setText(
                    f"Update available: v{info['latest']} (you have v{info['current']}). "
                    "Use the update banner in the main window to download and install."
                )
            else:
                self.upd_status.setText(
                    f"You are on the latest version (v{info['current']})."
                )

        def _failed(message):
            self.upd_btn.setEnabled(True)
            self.upd_status.setText(f"Update check failed: {message}")

        self._upd_worker.done.connect(_done)
        self._upd_worker.failed.connect(_failed)
        self._upd_worker.start()

    # -------------------------------------------------------------- license
    def _check_license(self) -> None:
        key = self.license.text().strip()
        info = verify_key(key)
        if not key:
            self.license_status.setText(
                "Unregistered - certificates will be marked as unregistered copy."
            )
        elif info and not info.get("expired"):
            self.license_status.setText(
                f"Licensed to {info['name']} until {info['expires']}."
            )
        elif info and info.get("expired"):
            self.license_status.setText("License expired.")
        else:
            self.license_status.setText("Invalid license key.")

    # --------------------------------------------------------------- values
    def values(self) -> dict:
        return {
            "google_api_key": self.google_key.text().strip(),
            "google_cx": self.google_cx.text().strip(),
            "brave_api_key": self.brave_key.text().strip(),
            "serper_api_key": self.serper_key.text().strip(),
            "tavily_api_key": self.tavily_key.text().strip(),
            "exa_api_key": self.exa_key.text().strip(),
            "searxng_url": self.searxng_url.text().strip(),
            "cross_verify_providers": self.cross_verify.isChecked(),
            "min_match_words": self.min_words.value(),
            "max_queries": self.max_queries.value(),
            "enable_web": self.enable_web.isChecked(),
            "enable_academic": self.enable_academic.isChecked(),
            "enable_ai": self.enable_ai.isChecked(),
            "exclude_quotes": self.exclude_quotes.isChecked(),
            "enable_semantic": self.enable_semantic.isChecked(),
            "license_key": self.license.text().strip(),
            "strictness": self.strictness.currentData() or "strict",
            "auto_update_check": self.auto_update_check.isChecked(),
            "auto_update_download": self.auto_update_download.isChecked(),
        }
