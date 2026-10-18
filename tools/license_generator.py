"""
Attribo — offline license generator (owner tool).

Issues the same HMAC-signed keys the app verifies fully offline.
GUI doubles as a mini admin console: single key, batch, verify.

Usage:
    python tools/license_generator.py                              # GUI
    python tools/license_generator.py "Friend Name" [YYYY-MM-DD]   # one key to stdout
    python tools/license_generator.py --batch names.txt [YYYY-MM-DD]
    python tools/license_generator.py --verify AI-NAME-2027-12-31-5E4D3C2B1A

(c) 2026 Attribo. All rights reserved.
"""
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from attribo.licensing.keycheck import make_key, verify_key  # noqa: E402

USAGE = __doc__.strip().split("Usage:")[1].strip()


def _default_expiry() -> str:
    return f"{datetime.date.today().year + 1}-12-31"


def _clean_names(text: str) -> list:
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _cli(argv: list) -> int:
    if argv[0] in ("-h", "--help"):
        print(USAGE)
        return 0

    if argv[0] == "--verify":
        if len(argv) < 2:
            print("usage: --verify <KEY>", file=sys.stderr)
            return 1
        info = verify_key(argv[1])
        if not info:
            print("INVALID — signature does not match.")
            return 1
        state = "EXPIRED" if info["expired"] else "VALID"
        print(f"{state} — name: {info['name']}, expires: {info['expires']}")
        return 0 if not info["expired"] else 2

    if argv[0] == "--batch":
        if len(argv) < 2:
            print("usage: --batch <names.txt> [YYYY-MM-DD]", file=sys.stderr)
            return 1
        src = Path(argv[1])
        if not src.exists():
            print(f"file not found: {src}", file=sys.stderr)
            return 1
        expires = argv[2] if len(argv) > 2 else _default_expiry()
        names = _clean_names(src.read_text(encoding="utf-8"))
        if not names:
            print("no names in file", file=sys.stderr)
            return 1
        for nm in names:
            print(f"{nm}\t{make_key(nm, expires)}")
        print(f"# {len(names)} keys, expiry {expires}", file=sys.stderr)
        return 0

    name = argv[0]
    expires = argv[1] if len(argv) > 1 else _default_expiry()
    print(make_key(name, expires))
    return 0


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
def _ensure_app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Attribo License Generator")
    from attribo.theme import QSS

    app.setStyleSheet(QSS)
    return app


def _build_window():
    from PySide6.QtCore import QDate, Qt, QTimer
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import (
        QDateEdit,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    from attribo import COPYRIGHT
    from attribo.theme import DANGER, MUTED, SUCCESS

    _ensure_app()

    win = QMainWindow()
    win.setWindowTitle("Attribo — License Generator")
    win.setFixedSize(640, 600)

    root = QWidget()
    win.setCentralWidget(root)
    outer = QVBoxLayout(root)
    outer.setContentsMargins(18, 16, 18, 14)
    outer.setSpacing(12)

    # ---- header ----------------------------------------------------------
    head = QHBoxLayout()
    brand = QLabel("Attribo")
    brand.setObjectName("BrandText2")
    what = QLabel("License Generator")
    what.setObjectName("H2")
    offline = QLabel("offline · HMAC-SHA256 · no phone-home")
    offline.setObjectName("Muted")
    head.addWidget(brand)
    head.addWidget(what)
    head.addStretch(1)
    head.addWidget(offline)
    outer.addLayout(head)

    def card() -> QVBoxLayout:
        frame = QFrame()
        frame.setObjectName("Card")
        outer.addWidget(frame)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(9)
        return lay

    # ---- single key ------------------------------------------------------
    c1 = card()
    t1 = QLabel("Issue a key")
    t1.setObjectName("H2")
    c1.addWidget(t1)
    grid = QGridLayout()
    grid.setHorizontalSpacing(10)
    name_edit = QLineEdit()
    name_edit.setPlaceholderText("Friend's name (e.g. Alice)")
    expiry_edit = QDateEdit()
    expiry_edit.setCalendarPopup(True)
    nxt = datetime.date.today().year + 1
    expiry_edit.setDate(QDate(nxt, 12, 31))
    expiry_edit.setDisplayFormat("yyyy-MM-dd")
    grid.addWidget(QLabel("Name"), 0, 0)
    grid.addWidget(name_edit, 0, 1)
    grid.addWidget(QLabel("Expires"), 0, 2)
    grid.addWidget(expiry_edit, 0, 3)
    grid.setColumnStretch(1, 2)
    grid.setColumnStretch(3, 1)
    c1.addLayout(grid)
    row = QHBoxLayout()
    gen_btn = QPushButton("Generate")
    gen_btn.setObjectName("Primary")
    key_out = QLineEdit()
    key_out.setReadOnly(True)
    key_out.setPlaceholderText("Key appears here — friend enters it in Settings → License")
    copy_btn = QPushButton("Copy")
    row.addWidget(gen_btn)
    row.addWidget(key_out, 1)
    row.addWidget(copy_btn)
    c1.addLayout(row)
    status1 = QLabel("")
    status1.setObjectName("Muted")
    c1.addWidget(status1)

    # ---- batch -----------------------------------------------------------
    c2 = card()
    t2 = QLabel("Batch issue")
    t2.setObjectName("H2")
    c2.addWidget(t2)
    batch_in = QPlainTextEdit()
    batch_in.setPlaceholderText("One name per line — blank lines and # comments are ignored")
    batch_in.setFixedHeight(70)
    names_out = QPlainTextEdit()
    names_out.setReadOnly(True)
    names_out.setFixedHeight(90)
    names_out.setPlaceholderText("name → key")
    brow = QHBoxLayout()
    bgen = QPushButton("Generate all")
    bcopy = QPushButton("Copy all")
    bsave = QPushButton("Save…")
    brow.addWidget(bgen)
    brow.addWidget(bcopy)
    brow.addWidget(bsave)
    brow.addStretch(1)
    c2.addWidget(batch_in)
    c2.addLayout(brow)
    c2.addWidget(names_out)

    # ---- verify ----------------------------------------------------------
    c3 = card()
    t3 = QLabel("Verify a key")
    t3.setObjectName("H2")
    c3.addWidget(t3)
    vrow = QHBoxLayout()
    vedit = QLineEdit()
    vedit.setPlaceholderText("AI-NAME-2027-12-31-SIGNATURE")
    vbtn = QPushButton("Verify")
    vrow.addWidget(vedit, 1)
    vrow.addWidget(vbtn)
    c3.addLayout(vrow)
    vstatus = QLabel("")
    vstatus.setObjectName("Muted")
    c3.addWidget(vstatus)

    # ---- footer ----------------------------------------------------------
    foot = QLabel(f"{COPYRIGHT}  ·  same scheme as tools/genkey.py")
    foot.setObjectName("Muted")
    foot.setAlignment(Qt.AlignRight)
    outer.addWidget(foot)

    # ---- behaviour ---------------------------------------------------------
    def flash(label: QLabel, text: str, color: str = "") -> None:
        label.setText(text)
        label.setStyleSheet(f"color: {color}" if color else f"color: {MUTED}")
        if color:
            QTimer.singleShot(2500, lambda: label.setText(""))

    def do_generate() -> None:
        name = name_edit.text().strip()
        if not name:
            flash(status1, "Enter a name first.", DANGER)
            return
        key = make_key(name, expiry_edit.date().toString("yyyy-MM-dd"))
        key_out.setText(key)
        key_out.setCursorPosition(0)
        flash(status1, "Key issued — send it to your friend.", SUCCESS)

    def do_copy() -> None:
        if key_out.text():
            QGuiApplication.clipboard().setText(key_out.text())
            flash(status1, "Copied to clipboard.", SUCCESS)

    def do_batch() -> None:
        names = _clean_names(batch_in.toPlainText())
        if not names:
            flash(status1, "Add at least one name to the batch box.", DANGER)
            return
        expires = expiry_edit.date().toString("yyyy-MM-dd")
        lines = [f"{nm}\t{make_key(nm, expires)}" for nm in names]
        names_out.setPlainText("\n".join(lines))
        flash(status1, f"{len(names)} key(s) generated, expiry {expires}.", SUCCESS)

    def do_copy_all() -> None:
        if names_out.toPlainText():
            QGuiApplication.clipboard().setText(names_out.toPlainText())
            flash(status1, "Batch copied to clipboard.", SUCCESS)

    def do_save() -> None:
        if not names_out.toPlainText():
            flash(status1, "Nothing to save — generate the batch first.", DANGER)
            return
        default = str(Path.home() / f"attribo_keys_{datetime.date.today().isoformat()}.txt")
        path, _ = QFileDialog.getSaveFileName(win, "Save keys", default, "Text files (*.txt)")
        if path:
            Path(path).write_text(names_out.toPlainText() + "\n", encoding="utf-8")
            flash(status1, f"Saved to {path}", SUCCESS)

    def do_verify() -> None:
        info = verify_key(vedit.text().strip())
        if not info:
            vstatus.setText("INVALID — signature does not match.")
            vstatus.setStyleSheet(f"color: {DANGER}")
            return
        if info["expired"]:
            vstatus.setText(f"VALID but EXPIRED — {info['name']}, ended {info['expires']}.")
            vstatus.setStyleSheet(f"color: {MUTED}")
        else:
            vstatus.setText(f"VALID — {info['name']}, expires {info['expires']}.")
            vstatus.setStyleSheet(f"color: {SUCCESS}")

    gen_btn.clicked.connect(do_generate)
    name_edit.returnPressed.connect(do_generate)
    copy_btn.clicked.connect(do_copy)
    bgen.clicked.connect(do_batch)
    bcopy.clicked.connect(do_copy_all)
    bsave.clicked.connect(do_save)
    vbtn.clicked.connect(do_verify)
    vedit.returnPressed.connect(do_verify)

    return win


def _gui() -> int:
    app = _ensure_app()
    win = _build_window()
    win.show()
    return app.exec()


def main(argv: list = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        return _cli(argv)
    return _gui()


if __name__ == "__main__":
    raise SystemExit(main())
