# Copyright & Third-Party Licenses — Attribo

> © 2026 Ayush Gupta (Attribo). All rights reserved.

## Ownership

- **Project name:** Attribo
- **Author / copyright holder:** Ayush Gupta
- **Year of first publication:** 2026
- All original source code, documentation, UI design, and report/certificate designs in this
  repository are the property of Ayush Gupta (project "Attribo") and are covered by the LICENSE
  file at the repository root (proprietary, personal use by authorized individuals).

## Third-party components

This software depends on open-source libraries. Their licenses are respected as follows
(no code has been copied into this repository; dependencies are installed).

| Component | License | Notes |
|---|---|---|
| PySide6 (Qt for Python) | LGPL-3.0 | Dynamically linked, unmodified — permitted for proprietary apps; do not statically link |
| python-docx | MIT | — |
| pypdf | BSD-3-Clause | Chosen over AGPL PDF libraries deliberately |
| requests | Apache-2.0 | — |
| beautifulsoup4 | MIT | — |
| ReportLab | BSD-3-Clause | Open-source version |
| qrcode | BSD | — |
| Pillow | HPND (MIT-style) | Pulled in by `qrcode[pil]` |

### License hygiene rules for contributors

1. Never add a dependency with a copyleft license that reaches the distributed product
   (AGPL/GPL) — e.g. **do not** swap pypdf for PyMuPDF (AGPL).
2. Don't bundle fonts, icons, or datasets without checking their license.
3. Keep this table updated whenever `requirements.txt` changes.

## Trademarks

AutoCAD, ZWCAD, Turnitin, iThenticate, Google, Brave, OpenAlex, Crossref, Microsoft Word are
trademarks of their respective owners. This project is not affiliated with or endorsed by any
of them.

---
*© 2026 Ayush Gupta (Attribo). All rights reserved.*
