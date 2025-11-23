import os
import time
import re
import requests
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('file_watcher.log'),
        logging.StreamHandler()
    ]
)

# URL для POST запроса
API_URL = "https://otlglcc10g.execute-api.ap-south-1.amazonaws.com/api/statements/upload"

# Паттерн для имени файла: 3-4 буквы + "__" + что угодно
FILE_PATTERN = re.compile(r'^[A-Z]{3,4}__.*', re.IGNORECASE)

# Папка Downloads
DOWNLOADS_FOLDER = str(Path.home() / "Downloads")

# Множество обработанных файлов (чтобы не отправлять повторно)
processed_files = set()


class DownloadsHandler(FileSystemEventHandler):
    """Обработчик событий файловой системы"""
    
    def on_created(self, event):
        """Вызывается когда файл создан"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_name = os.path.basename(file_path)
        
        # Проверяем паттерн имени файла
        if FILE_PATTERN.match(file_name):
            logging.info(f"Обнаружен новый файл: {file_name}")
            # Ждем немного, чтобы файл полностью загрузился
            time.sleep(2)
            self.upload_file(file_path, file_name)
    
    def on_modified(self, event):
        """Вызывается когда файл изменен (тоже может означать завершение загрузки)"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_name = os.path.basename(file_path)
        
        # Проверяем паттерн и что файл еще не обработан
        if FILE_PATTERN.match(file_name) and file_path not in processed_files:
            # Проверяем, что файл полностью загружен
            if self.is_file_complete(file_path):
                logging.info(f"Файл завершен: {file_name}")
                self.upload_file(file_path, file_name)
    
    def is_file_complete(self, file_path):
        """Проверяет, завершена ли загрузка файла"""
        try:
            # Проверяем размер файла дважды с интервалом
            size1 = os.path.getsize(file_path)
            time.sleep(1)
            size2 = os.path.getsize(file_path)
            return size1 == size2 and size1 > 0
        except:
            return False
    
    def upload_file(self, file_path, file_name):
        """Отправляет файл на сервер"""
        if file_path in processed_files:
            return
        
        try:
            # Проверяем что файл существует и можем его открыть
            if not os.path.exists(file_path):
                logging.warning(f"Файл не найден: {file_path}")
                return
            
            logging.info(f"Отправка файла {file_name} на {API_URL}")
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f)}
                response = requests.post(API_URL, files=files, timeout=30)
            
            if response.status_code == 200:
                logging.info(f"✓ Файл {file_name} успешно отправлен!")
                logging.info(f"Ответ сервера: {response.text}")
                processed_files.add(file_path)
            else:
                logging.error(f"✗ Ошибка при отправке {file_name}. Код: {response.status_code}")
                logging.error(f"Ответ: {response.text}")
        
        except Exception as e:
            logging.error(f"✗ Исключение при отправке файла {file_name}: {str(e)}")


def scan_existing_files():
    """Сканирует существующие файлы в папке Downloads при запуске"""
    logging.info("Сканирование существующих файлов в Downloads...")
    
    try:
        for file_name in os.listdir(DOWNLOADS_FOLDER):
            file_path = os.path.join(DOWNLOADS_FOLDER, file_name)
            
            # Пропускаем директории
            if os.path.isdir(file_path):
                continue
            
            # Проверяем паттерн
            if FILE_PATTERN.match(file_name):
                logging.info(f"Найден существующий файл: {file_name}")
                # Не отправляем существующие файлы, просто добавляем в обработанные
                processed_files.add(file_path)
    
    except Exception as e:
        logging.error(f"Ошибка при сканировании: {str(e)}")


def main():
    """Главная функция"""
    print("=" * 60)
    print("   МОНИТОРИНГ ПАПКИ DOWNLOADS")
    print("=" * 60)
    print(f"Папка: {DOWNLOADS_FOLDER}")
    print(f"API URL: {API_URL}")
    print(f"Паттерн файлов: 3-4 буквы + '__' + название")
    print("Примеры: BOI__report.xlsx, IDB__data.csv")
    print("=" * 60)
    print("\nПриложение запущено! Нажмите Ctrl+C для остановки.\n")
    
    # Проверяем существование папки Downloads
    if not os.path.exists(DOWNLOADS_FOLDER):
        logging.error(f"Папка Downloads не найдена: {DOWNLOADS_FOLDER}")
        return
    
    # Сканируем существующие файлы (чтобы не отправлять их)
    scan_existing_files()
    
    # Создаем обработчик и наблюдатель
    event_handler = DownloadsHandler()
    observer = Observer()
    observer.schedule(event_handler, DOWNLOADS_FOLDER, recursive=False)
    observer.start()
    
    logging.info("✓ Мониторинг активен. Ожидание новых файлов...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("\nОстановка мониторинга...")
        observer.stop()
    
    observer.join()
    logging.info("Приложение завершено.")


if __name__ == "__main__":
    main()

