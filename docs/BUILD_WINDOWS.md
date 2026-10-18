# Building the Windows Installer — Attribo

> © 2026 Attribo. All rights reserved.

Produces: `dist\Attribo\` (onedir build) → `Attribo_Setup.exe` via Inno Setup.

## 0. Prerequisites

- Windows 10/11 x64
- Python 3.10–3.12 (`python --version`)
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) (free) for the installer step

## 1. One-time setup

```powershell
cd "Attribo-Attribo"
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

## 2. Test run before packaging

```powershell
python tests\smoke_test.py      # offline sanity check (no network needed)
python run.py                   # launch the app
```

## 3. Build the app folder (PyInstaller, onedir)

Use onedir (NOT onefile): faster startup, fewer antivirus false positives.

```powershell
pyinstaller --noconfirm --clean --windowed --name Attribo --icon "packaging\appicon.ico" --collect-all qrcode --collect-all onnxruntime run.py
```

Notes:

- `--windowed` hides the console. For debugging builds, drop it to see errors.
- `--icon packaging\appicon.ico` brands the exe (installer + shortcuts inherit it).
- `--collect-all onnxruntime` bundles the optional semantic-layer runtime (model file
  is still downloaded on first use, ~90 MB).
- Results land in `dist\Attribo\`. Launch `Attribo.exe` inside it to verify.
- Typical size: ~200 MB on disk (Qt + onnxruntime). That is normal for Qt apps.

Or simply run the helper script:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build.ps1
```

## 4. Build the installer (Inno Setup)

1. Open `packaging\installer.iss` in Inno Setup Compiler.
2. Optionally change `AppPublisher`, version, and icon.
3. Compile → output `dist\installer\Attribo_Setup.exe`.

Or from the command line (after `winget install JRSoftware.InnoSetup`):

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" packaging\installer.iss
```

The installer is **per-user** (no admin prompt), installs to `%LOCALAPPDATA%\Programs\Attribo`,
creates Start Menu + Desktop shortcuts, and registers an uninstaller. Typical Setup.exe size: ~57 MB.

## 5. SmartScreen warning (expected until code signing)

Unsigned installers trigger "Windows protected your PC". Friends can click
**More info → Run anyway**. To remove the warning you need a code-signing certificate
(≈ $100–400/yr, e.g. from a CA or Azure Trusted Signing) and then:

```powershell
signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 dist\installer\Attribo_Setup.exe
```

## 6. Versioning & distribution checklist

- [ ] Bump `__version__` in `attribo\__init__.py`
- [ ] Update `docs\CHANGELOG.md`
- [ ] Rebuild + test on a clean PC (no Python installed) — this catches missing DLLs
- [ ] Generate a license key for each friend: open `tools\license_generator.py`
      (GUI, or `python tools\genkey.py "Friend Name" 2027-12-31` for scripting)
- [ ] Share the installer + their key (key entry: Settings → License)

## 7. Common packaging problems

| Symptom | Fix |
|---|---|
| App won't start on a clean PC | Missing MSVC runtime — test on clean machine; Inno installer can bundle VC++ redist |
| Antivirus flags the exe | Rebuild onedir (not onefile); submit to Microsoft for whitelisting; consider signing |
| Qt platform plugin error | Ensure PyInstaller collected PySide6 plugins (default with recent PyInstaller) |
| Fonts look wrong | Windows built-in fonts are fine; custom fonts would need bundling via `--add-data` |

---
*© 2026 Attribo. All rights reserved.*
