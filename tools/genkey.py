"""
Generate offline license keys for Attribo.

Usage:
    python tools/genkey.py "Friend Name" [YYYY-MM-DD]

(c) 2026 Attribo. All rights reserved.
"""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from attribo.licensing.keycheck import make_key  # noqa: E402


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "Friend"
    if len(sys.argv) > 2:
        expires = sys.argv[2]
    else:
        expires = f"{datetime.date.today().year + 1}-12-31"
    print(make_key(name, expires))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
