@echo off
echo Running hero-dbc extract script...
echo.

REM Set the correct paths
set WOW_DIR="C:\Program Files (x86)\World of Warcraft\_retail_"
set SIMC_DIR="C:\Users\joshu\OneDrive\Documents\GitHub\simc"
set PYTHON_EXE="C:\Users\joshu\AppData\Local\Programs\Python\Python314\python.exe"

REM Change to the scripts directory
cd /d "%~dp0"

REM Run the extract script with the correct paths
%PYTHON_EXE% extract.py --wowdir %WOW_DIR% --simcdir %SIMC_DIR% --simc

echo.
echo Extract script completed.
pause
