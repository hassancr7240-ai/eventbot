@echo off
title EventBot Pro — Run Now
echo ================================================
echo   EventBot Pro — Running full scrape
echo   Venues: ALL  |  Years: current to +3
echo ================================================
echo.
cd /d "%~dp0"
python scheduler.py --run-now
echo.
echo Done. Excel file saved in output\ folder.
pause
