@echo off
echo Installing requirements...
pip install -r requirements.txt

echo Building launcher...
pyinstaller --noconfirm --onefile --windowed launcher/main.py --icon=assets/logo.png

echo Done. Executable should be in the dist\ folder.
pause
