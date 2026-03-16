@echo off
echo ============================================
echo   Quantitative Trading Signal Engine
echo ============================================
echo.

echo [1/3] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Download from python.org
    pause
    exit
)

echo.
echo [2/3] Installing dependencies...
python.exe -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo First attempt failed. Retrying with --only-binary flag...
    pip install pandas numpy --only-binary :all:
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Install still failed. See error above.
        pause
        exit
    )
)
echo Dependencies installed successfully.

echo.
echo [3/3] Seeding database with live data...
python run.py --once
if errorlevel 1 (
    echo ERROR: Pipeline failed. Check your .env file and internet connection.
    pause
    exit
)

echo.
echo ============================================
echo   Launching Streamlit app...
echo   Open your browser to: http://localhost:8501
echo ============================================
echo.
streamlit run app.py
pause
