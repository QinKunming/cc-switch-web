@echo off
rem cc-switch-web launcher: cd to this script's dir so it works from anywhere
cd /d "%~dp0"
python server.py
if errorlevel 1 pause
