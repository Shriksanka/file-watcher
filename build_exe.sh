#!/bin/bash

echo "===================================="
echo "Building FileWatcher executable"
echo "===================================="
echo ""

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Building executable..."
pyinstaller --onefile --name FileWatcher --console file_watcher.py

echo ""
echo "===================================="
echo "Build complete!"
echo "===================================="
echo "Executable location: dist/FileWatcher"
echo ""

deactivate

