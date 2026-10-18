"""
Attribo logo exporter - renders the brand mark (attribo.ui.branding) and
writes the distributable assets:

  - packaging/appicon.ico   (16-256px multi-size; exe / window / installer)
  - docs/assets/logo.png    (512px; README & docs)

Usage:  python tools\\make_logo.py
(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QGuiApplication  # noqa: E402

from attribo.ui import branding  # noqa: E402

ICO_PATH = ROOT / "packaging" / "appicon.ico"
PNG_PATH = ROOT / "docs" / "assets" / "logo.png"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    del app

    from PIL import Image

    tmp_dir = ROOT / "build" / "logo_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for size in ICO_SIZES:
        path = tmp_dir / f"logo_{size}.png"
        branding.logo_image(size).save(str(path), "PNG")
        frames.append(Image.open(path).convert("RGBA"))
        print(f"rendered {size}px")

    docs_png = branding.logo_image(512)
    PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    docs_png.save(str(PNG_PATH), "PNG")
    print("saved:", PNG_PATH)

    base = frames[-1]  # 256px frame as base
    try:
        base.save(str(ICO_PATH), format="ICO", append_images=frames[:-1])
    except (TypeError, ValueError):
        base.save(str(ICO_PATH), format="ICO", sizes=[(s, s) for s in ICO_SIZES])
    print("saved:", ICO_PATH)

    with Image.open(ICO_PATH) as check:
        sizes = sorted({w for (w, _h) in check.ico.sizes()}) if hasattr(check, "ico") else []
        print("ico sizes:", sizes or "written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
