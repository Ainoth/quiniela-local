@echo off
cd /d "%~dp0"
if not exist .venv-studio\Scripts\python.exe (
  py -3 -m venv .venv-studio
  if errorlevel 1 exit /b 1
  .venv-studio\Scripts\python.exe -m pip install -e ".[test]"
  if errorlevel 1 exit /b 1
)
.venv-studio\Scripts\python.exe -c "import PySide6, platformdirs" >nul 2>nul
if errorlevel 1 (
  .venv-studio\Scripts\python.exe -m pip install -e ".[test]"
  if errorlevel 1 exit /b 1
)
set "PYTHONPATH=%CD%\src;%CD%;%PYTHONPATH%"
.venv-studio\Scripts\python.exe -m quiniela_ai_studio %*
