@echo off
REM ML Model Setup Script for Windows
REM Run this after cloning the repository or on deployment

echo ============================================
echo ML Model Setup for Fora
echo ============================================
echo.

REM Check if we're in the server directory
if not exist "train_with_sample_data.py" (
    echo Changing to server directory...
    cd server
)

REM Install dependencies if needed
echo Installing dependencies...
pip install -q -r requirements.txt

REM Train the model
echo.
echo Training ML model with sample data...
echo.
python train_with_sample_data.py

echo.
echo ============================================
echo ML Model Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Start the server: uvicorn app.main:app --reload
echo 2. Check model_info.txt for training details
echo 3. Set up scheduled tasks for periodic retraining
echo.
