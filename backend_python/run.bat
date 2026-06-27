@echo off
echo Setting up Python environment...

IF NOT EXIST myenv (
    echo Creating virtual environment 'myenv'...
    python -m venv myenv
) ELSE (
    echo Virtual environment 'myenv' already exists.
)

echo Activating virtual environment...
call myenv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo Installing Playwright browsers...
python -m playwright install chromium

echo Ready to Start Server