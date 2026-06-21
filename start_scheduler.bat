@echo off
title EventBot Pro — Auto Scheduler
echo ================================================
echo   EventBot Pro — Auto Scheduler
echo   Runs daily at 6:00 AM
echo   Keep this window open for automatic scheduling
echo ================================================
echo.
cd /d "%~dp0"
python scheduler.py
pause
