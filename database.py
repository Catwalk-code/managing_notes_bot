#Для работы с БД
"""Этот файл содержит функции для взаимодействия с базой данных SQLite.
 Используется для хранения заметок и напоминаний пользователей"""

import sqlite3
import os
from datetime import datetime
import time
from dotenv import load_dotenv
import threading

# Загружаем переменные окружения из .env файла
load_dotenv()

# Путь к файлу базы данных
db_path = os.getenv("DATABASE_PATH")

# Создаём объект блокировки для безопасной работы с базой данных из разных потоков
db_lock = threading.Lock()

def init_db():
    # Проверяет, что файл базы существует. Таблицы созданы вручную.
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"База данных {db_path} не найдена.")
    print("База данных найдена.")

def add_note(user_id, title, content):
    # Добавление новой заметки
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)', (user_id, title, content))
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return note_id

def get_all_notes(user_id):
    # Получение всех заметок пользователя
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, content, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    notes = cursor.fetchall()
    conn.close()
    return notes

def delete_note(user_id, note_id):
    # Удаление заметки пользователя
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE user_id = ? AND id = ?', (user_id, note_id))
    conn.commit()
    conn.close()

def get_all_reminders():
    # Получение всех напоминаний
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, note_id, reminder_time, message, is_sent FROM reminders')
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def mark_reminder_as_sent(reminder_id):
    # Помечает напоминание как отправленное
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE reminders SET is_sent = TRUE WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()

def delete_all_user_notes(user_id):
    # Удаляет все заметки пользователя
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def add_reminder(user_id, note_id, reminder_time, message):
    # Добавляет напоминание в БД
    print(f"DEBUG: Добавляем напоминание в БД: user_id={user_id}, note_id={note_id}, time={reminder_time}, message={message}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reminders (user_id, note_id, reminder_time, message)
        VALUES (?, ?, ?, ?)
    ''', (user_id, note_id, reminder_time, message))
    conn.commit()
    conn.close()
    print("DEBUG: Напоминание добавлено.")

def delete_reminder(reminder_id, user_id):
    # Удаляет напоминание из БД (только если оно принадлежит пользователю)
    with db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?', (reminder_id, user_id))
        changes = cursor.rowcount  # Сколько строк было удалено
        conn.commit()
        conn.close()
        return changes > 0  # Возвращает True, если удаление прошло успешно

def get_user_reminders(user_id):
    # Получение всех напоминаний пользователя
    with db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, note_id, reminder_time, message, is_sent FROM reminders WHERE user_id = ?', (user_id,))
        reminders = cursor.fetchall()
        conn.close()
        return reminders
    
def delete_all_user_reminders(user_id):
    # Удаляет все напоминания пользователя
    with db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reminders WHERE user_id = ?', (user_id,))
        changes = cursor.rowcount
        conn.commit()
        conn.close()
        return changes  # Возвращает количество удалённых строк

def check_and_send_reminders(bot):
    # Проверяет и отправляет напоминания
    # Эта функция запускается в отдельном потоке и работает постоянно.
    while True:
        try:
            reminders_list = get_all_reminders()
            current_time = datetime.now()
            
            for reminder in reminders_list:
                reminder_id, user_id, note_id, reminder_time_str, message, is_sent = reminder
                
                # Пропускаем уже отправленные напоминания
                if is_sent:
                    continue
                
                # Преобразуем строку времени в объект datetime (только с секундами)
                try:
                    reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Если формат неверный, пропускаем
                    print(f"Неверный формат времени: {reminder_time_str}. Ожидается YYYY-MM-DD HH:MM:SS")
                    continue
                
                # Если время напоминания настало или уже прошло
                if current_time >= reminder_time:
                    # Отправляем сообщение пользователю
                    try:
                        bot.send_message(user_id, f"Напоминание: {message}")
                    except Exception as e:
                        print(f"Ошибка отправки напоминания пользователю {user_id}: {e}")
                    
                    # Помечаем напоминание как отправленное
                    mark_reminder_as_sent(reminder_id)
        except Exception as e:
            print(f"Ошибка при проверке напоминаний: {e}")
        
        # Проверяем каждые 60 секунд
        time.sleep(60)