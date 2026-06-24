@echo off
REM EventBot Local Runner - Just double-click this file!

echo Starting EventBot locally...
echo.
echo Installing dependencies...
python -m pip install -r requirements.txt -q

echo.
echo Launching Streamlit app...
echo.
echo Open your browser at: http://localhost:8501
echo Password: workrbee2026
echo.
echo Press Ctrl+C in this window to stop
echo.

python -m streamlit run app.py

pause
