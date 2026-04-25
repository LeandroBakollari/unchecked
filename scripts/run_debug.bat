@echo off
setlocal
cd /d "%~dp0.."
set PYTHONDONTWRITEBYTECODE=1

py -m game.main --windowed --debug-hitboxes --width 1280 --height 850
