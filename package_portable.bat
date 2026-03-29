@echo off
setlocal
cd /d "%~dp0"

if not exist ".\dist\Unchecked\Unchecked.exe" (
    echo Missing .\dist\Unchecked\Unchecked.exe
    echo Build the executable first with PyInstaller, then run this packaging script.
    pause
    exit /b 1
)

if exist ".\portable" rmdir /s /q ".\portable"
mkdir ".\portable\Unchecked"

copy ".\run.bat" ".\portable\Unchecked\run.bat" >nul
xcopy /e /i /y ".\dist\Unchecked" ".\portable\Unchecked" >nul

powershell -NoProfile -Command "Compress-Archive -Path '.\portable\Unchecked\*' -DestinationPath '.\portable\Unchecked-portable.zip' -Force"

echo Portable package created:
echo .\portable\Unchecked-portable.zip
pause
