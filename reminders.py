"""Этот файл отвечает за запуск фонового потока, который проверяет и отправляет напоминания"""
import threading
import time
from database import get_all_reminders, check_and_send_reminders

# Запускает поток для проверки напоминаний
def start_reminder_thread():
    # Импортируем bot из main.py, чтобы избежать циклического импорта
    from main import bot
    reminder_thread = threading.Thread(target=check_and_send_reminders, args=(bot,), daemon=True)
    reminder_thread.start()