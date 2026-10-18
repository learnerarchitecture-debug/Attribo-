"""
Dark modern theme — palette constants + Qt stylesheet.
(c) 2026 Attribo. All rights reserved.
"""

BG = "#0B0E13"
SURFACE = "#121722"
SURFACE2 = "#161C28"
BORDER = "#232B3A"
TEXT = "#E8EDF4"
MUTED = "#8A94A6"
ACCENT = "#5B8CFF"
ACCENT2 = "#8B5CF6"
SUCCESS = "#34D399"
WARN = "#FBBF24"
DANGER = "#F87171"
CYAN = "#22D3EE"

QSS = f"""
* {{ font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif; }}

QMainWindow, QDialog {{ background-color: {BG}; }}
QWidget {{ color: {TEXT}; font-size: 13px; }}

QLabel#BrandText {{ font-size: 19px; font-weight: 700; color: {TEXT}; }}
QLabel#BrandText2 {{ font-size: 19px; font-weight: 700; color: {ACCENT}; }}
QLabel#Muted {{ color: {MUTED}; }}
QLabel#H2 {{ font-size: 14px; font-weight: 600; }}
QLabel#Big {{ font-size: 22px; font-weight: 700; }}

QFrame#Header {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #10151F, stop:0.5 #131B2C, stop:1 #10151F);
    border-bottom: 1px solid {BORDER};
}}
QFrame#Card {{ background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; }}

QPushButton {{
    background-color: {SURFACE2}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 9px;
    padding: 8px 14px;
}}
QPushButton:hover {{ background-color: #1D2534; border-color: #2E3950; }}
QPushButton:pressed {{ background-color: #182032; }}
QPushButton:disabled {{ color: #5A6474; background-color: #141A24; border-color: #1E2634; }}

QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
    color: white; border: none; font-weight: 600;
    padding: 11px 18px; border-radius: 10px;
}}
QPushButton#Primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6E9AFF, stop:1 #9B6EF7);
}}
QPushButton#Primary:disabled {{ background: #232B3A; color: #5A6474; }}

QLineEdit, QSpinBox, QComboBox {{
    background-color: #0E131C; border: 1px solid {BORDER};
    border-radius: 8px; padding: 7px 10px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {ACCENT}; }}

QCheckBox {{ spacing: 8px; color: {TEXT}; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid #2E3950; background: #0E131C;
}}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QProgressBar {{
    background-color: #141A24; border: none; border-radius: 7px;
    height: 14px; text-align: center; color: {MUTED}; font-size: 10px;
}}
QProgressBar::chunk {{
    border-radius: 7px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
}}

QTabWidget::pane {{
    border: 1px solid {BORDER}; border-radius: 12px;
    background-color: {SURFACE}; top: -1px;
}}
QTabBar::tab {{
    background: transparent; color: {MUTED};
    padding: 8px 14px; border-radius: 8px; margin-right: 4px; margin-bottom: 6px;
}}
QTabBar::tab:selected {{ background-color: #1A2233; color: {TEXT}; font-weight: 600; }}
QTabBar::tab:hover {{ color: {TEXT}; }}

QTableWidget {{
    background-color: #0E131C; alternate-background-color: #10161F;
    gridline-color: #1B2331; border: 1px solid {BORDER}; border-radius: 10px;
}}
QHeaderView::section {{
    background-color: #121826; color: {MUTED};
    border: none; padding: 8px 6px;
}}
QTableWidget::item {{ padding: 6px; }}
QTableWidget::item:selected {{ background-color: #22304A; }}

QTextBrowser {{ background-color: #0E131C; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #2A3448; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #35425C; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #2A3448; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QStatusBar {{ background-color: #0D1119; color: {MUTED}; border-top: 1px solid {BORDER}; }}
QToolTip {{ background-color: #1A2233; color: {TEXT}; border: 1px solid {BORDER}; padding: 6px; }}
QMessageBox {{ background-color: {SURFACE}; }}
QMenu {{ background-color: {SURFACE}; border: 1px solid {BORDER}; }}
QMenu::item:selected {{ background-color: #22304A; }}

QPushButton#UpdateBanner {{
    background-color: #1B2A4A; color: #8FB4FF;
    border: 1px solid #2E4B85; border-radius: 10px;
    padding: 5px 12px; font-weight: 600;
}}
QPushButton#UpdateBanner:hover {{ background-color: #22355C; border-color: #3D63A8; }}
"""

# Colour code used everywhere a match type is shown (dark-mode friendly).
MATCH_COLORS = {
    "verbatim": "#FF5B5B",
    "near": "#FF9F40",
    "semantic": "#4DA3FF",
    "paraphrase": "#FACC15",
    "duplicate": "#C084FC",
}
MATCH_LABELS = {
    "verbatim": "Verbatim",
    "near": "Near-match",
    "semantic": "Semantic",
    "paraphrase": "Paraphrase",
    "duplicate": "Internal dup",
}
