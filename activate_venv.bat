@echo off
REM Activate virtual environment and start Python shell
cd /d "%~dp0"
call .\.venv\Scripts\activate.bat
echo.
echo Virtual environment activated!
echo Type 'deactivate' to exit the virtual environment
echo.
cmd /k
