@echo off
REM This script attempts to activate a virtual environment and run weeablind.py

SET VENV_NAME=venv
SET PYTHON_EXE=python

REM Check if the virtual environment directory exists
IF NOT EXIST "%VENV_NAME%\Scripts\activate.bat" (
    echo Virtual environment "%VENV_NAME%" not found or activate.bat is missing.
    echo Please ensure the virtual environment is created and named correctly,
    echo or modify the VENV_NAME variable in this script.
    echo Trying to run with system Python...
) ELSE (
    echo Activating virtual environment: %VENV_NAME%
    CALL "%VENV_NAME%\Scripts\activate.bat"
)

echo Starting Weeablind...
%PYTHON_EXE% weeablind.py

echo.
echo Weeablind has closed. If the virtual environment was activated,
echo you might need to type 'deactivate' or close this window.
pause
