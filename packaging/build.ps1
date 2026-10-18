# Attribo - build script  (c) 2026 Attribo
# Builds dist\Attribo\ with PyInstaller (onedir, windowed).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$python = "C:\apcvenv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

Write-Host "1/3 Installing dependencies..."
& $python -m pip install -r requirements.txt
& $python -m pip install pyinstaller

Write-Host "2/3 Running smoke test..."
& $python tests\smoke_test.py

Write-Host "3/3 Building executable (onedir)..."
& $python -m PyInstaller --noconfirm --clean --windowed --name Attribo --icon "packaging\appicon.ico" --collect-all qrcode --collect-all onnxruntime run.py

Write-Host ""
Write-Host "Build complete: dist\Attribo\Attribo.exe"
Write-Host "Next: compile packaging\installer.iss with Inno Setup 6 to get the Setup.exe."
