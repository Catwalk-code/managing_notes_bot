# Логика управления заметками
from config import bot
from telebot import types
# from database import ... # Импортируем функции из database, когда они будут готовы

# Обработчик команд. Каждое слово в кавычках внутри квадратных скобок соответствует определенной команде
@bot.message_handler(commands=['start'])
def start_bot(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    if last_name:
        full_name = f'{first_name} {last_name}'
    else:
        full_name = f'{first_name}'

    bot.send_message(message.chat.id, f'Привет, {full_name}!')

@bot.message_handler(commands=['help'])
def bot_help(message):
    bot.send_message(message.chat.id, '<b>Бот предназначен для создания Заметок.</b>', parse_mode='html')

@bot.message_handler(commands=['add'])
def add_note(message):
    bot.send_message(message.chat.id, 'добавить заметку')

@bot.message_handler(commands=['show'])
def show_note(message):
    bot.send_message(message.chat.id, 'Показать все созданные заметки')

@bot.message_handler(commands=['delete'])
def delete_note(message):
    bot.send_message(message.chat.id, 'Удалить одну заметку')

@bot.message_handler(commands=['clear'])
def delete_all_notes(message): # Лучше дать уникальное имя, а не 'delete'
    bot.send_message(message.chat.id, 'Удалить все заметки')