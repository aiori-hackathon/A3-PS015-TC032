@echo off
REM Starts the dashboard on Windows. Double-click this file.
cd /d "%~dp0"
if not exist .venv (
    echo Creating virtual environment...
    py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
pause
