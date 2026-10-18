@echo off
rem Attribo launcher - (c) 2026 Attribo
rem Uses the short-path virtual environment if present, else plain python.
setlocal
set VENV=C:\apcvenv
if exist "%VENV%\Scripts\python.exe" (
  "%VENV%\Scripts\python.exe" "%~dp0run.py" %*
) else (
  python "%~dp0run.py" %*
)
