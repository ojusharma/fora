@echo off
REM Setup script for ML recommendation engine (Windows)

echo =========================================
echo Fora ML Recommendation Engine Setup
echo =========================================
echo.

REM Install Python dependencies
echo Installing Python dependencies...
cd server
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Failed to install Python dependencies
    exit /b 1
)

echo Python dependencies installed
echo.

REM Generate sample data (optional)
set /p generate_sample="Would you like to generate sample training data? (y/n): "

if /i "%generate_sample%"=="y" (
    echo Generating sample data...
    python train_with_sample_data.py
    
    if %errorlevel% equ 0 (
        echo Sample data generated successfully
    ) else (
        echo Sample data generation failed ^(you can run this later^)
    )
)

echo.
echo =========================================
echo Setup Complete!
echo =========================================
echo.
echo The ML recommendation engine will:
echo   * Run automatically in the background when the server starts
echo   * Update recommendations every hour
echo   * Train on user interactions daily at 2 AM
echo.
echo To start the server:
echo   cd server
echo   python run.py
echo.
echo The home page will display personalized recommendations!
echo =========================================
pause
