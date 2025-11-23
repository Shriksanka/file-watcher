@echo off
echo ====================================
echo Building FileWatcher.exe
echo ====================================
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller --onefile --name FileWatcher --console file_watcher.py

echo.
echo ====================================
echo Build complete!
echo ====================================
echo EXE file location: dist\FileWatcher.exe
echo.
pause

