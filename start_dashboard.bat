@echo off
title EventBot Pro Dashboard
echo ================================================
echo   EventBot Pro — Starting Dashboard
echo   URL: http://localhost:8501
echo   Password: workrbee2026
echo ================================================
echo.
cd /d "%~dp0"
set EVENTBOT_PASSWORD=workrbee2026
python -m streamlit run app.py --server.port 8501 --server.headless false --server.address localhost
pause
