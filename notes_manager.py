""" Логика управления заметками
Этот файл содержит функции, которые работают с заметками и напоминаниями"""

from telebot import types
from database import init_db, add_note, get_all_notes, delete_note, delete_all_user_notes, get_user_reminders, delete_reminder, delete_all_user_reminders

def add_note_logic(user_id, title, content):
    # Добавляет заметку в БД
    return add_note(user_id, title, content)

def get_notes_logic(user_id):
    # Получает заметки из БД
    return get_all_notes(user_id)

def delete_note_logic(user_id, note_id):
    # Удаляет заметку из БД
    delete_note(user_id, note_id)

def delete_all_notes_logic(user_id):
    # Удаляет все заметки пользователя
    delete_all_user_notes(user_id)

def get_clear_confirmation_markup():
    # Создает клавиатуру для подтверждения удаления всех заметок
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Подтвердить удаление', callback_data='confirm_clear')
    markup.row(btn)
    return markup

def get_user_reminders_logic(user_id):
    # Получает напоминания пользователя из БД
    return get_user_reminders(user_id)

def delete_reminder_logic(reminder_id, user_id):
    # Удаляет напоминание из БД
    return delete_reminder(reminder_id, user_id)

def delete_all_reminders_logic(user_id):
    # Удаляет все напоминания пользователя
    return delete_all_user_reminders(user_id)

def get_clear_reminders_confirmation_markup():
    #Создает клавиатуру для подтверждения удаления всех напоминаний
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Подтвердить удаление', callback_data='confirm_clear_reminders')
    markup.row(btn)
    return markup