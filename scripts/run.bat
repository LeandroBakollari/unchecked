@echo off
setlocal
cd /d "%~dp0.."

if exist ".\dist\Unchecked\Unchecked.exe" (
    start "" ".\dist\Unchecked\Unchecked.exe"
    exit /b 0
)

if exist ".\Unchecked.exe" (
    start "" ".\Unchecked.exe"
    exit /b 0
)

if exist "%LocalAppData%\Programs\Python\Python311\pythonw.exe" (
    start "" "%LocalAppData%\Programs\Python\Python311\pythonw.exe" -m game.main
    exit /b 0
)

if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    start "" "%LocalAppData%\Programs\Python\Python311\python.exe" -m game.main
    exit /b 0
)

echo No packaged executable was found.
echo Build one first, or run with a local Python install.
pause
