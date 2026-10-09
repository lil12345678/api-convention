@echo off
setlocal
cd /d "%~dp0"

REM Prefer py launcher, then common install paths on this machine
set "PY="
where py >nul 2>nul && for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%i"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PY where python >nul 2>nul && for /f "delims=" %%i in ('where python') do (
  set "PY=%%i"
  goto :have_py
)

:have_py
if not defined PY (
  echo [ERROR] Python not found. Install Python 3.11+ and tick "Add to PATH".
  pause
  exit /b 1
)

echo Using Python: %PY%

REM Recreate venv if missing or pointing to a deleted Python
set "NEED_VENV=0"
if not exist ".venv\Scripts\python.exe" set "NEED_VENV=1"
if exist ".venv\pyvenv.cfg" (
  findstr /C:"Python314" ".venv\pyvenv.cfg" >nul 2>nul && set "NEED_VENV=1"
  findstr /C:"Users\lily\\" ".venv\pyvenv.cfg" >nul 2>nul && set "NEED_VENV=1"
)

if "%NEED_VENV%"=="1" (
  echo Recreating virtualenv ...
  if exist ".venv" rmdir /s /q ".venv"
  "%PY%" -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create .venv
    pause
    exit /b 1
  )
)

echo Installing dependencies ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed
  pause
  exit /b 1
)

echo Starting FastAPI on http://127.0.0.1:8000 ...
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
if errorlevel 1 (
  echo [ERROR] uvicorn exited with an error
  pause
  exit /b 1
)

pause
