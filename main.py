import webbrowser
import telebot
from telebot import types
from dotenv import load_dotenv
import os
import notes_manager
import reminders
from datetime import datetime
from database import init_db, add_note, get_all_notes, delete_note, delete_all_user_notes, add_reminder, get_user_reminders, delete_reminder
from notes_manager import get_notes_logic, add_note_logic, delete_note_logic, delete_all_notes_logic, get_clear_confirmation_markup, get_user_reminders_logic, delete_reminder_logic, delete_all_reminders_logic, get_clear_reminders_confirmation_markup

# Загружаем переменные окружения из .env файла
load_dotenv()
bot_token = os.getenv("TELEGRAM_API_TOKEN")
bot = telebot.TeleBot(bot_token)

# Инициализация базы данных
from database import init_db
init_db()

"Далее идут обработчики команд"
# /start
@bot.message_handler(commands=['start'])
def start_bot(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    if last_name:
        full_name = f'{first_name} {last_name}'
    else:
        full_name = f'{first_name}'

    bot.send_message(message.chat.id, '<b>Привет, {}</b>, воспользуйся командой {}, что бы узнать больше о боте!'.format(full_name, "/help"), parse_mode='html')

# /help - справка
@bot.message_handler(commands=['help'])
def bot_help(message):
    bot.send_message(message.chat.id, '<b>Бот предназначен для создания Заметок. Используйте кнопку "Меню" чтобы приступить к использованию функционала.</b>', parse_mode='html')

# /add для добавления заметки
@bot.message_handler(commands=['add'])
def add_note_command(message):
    msg = bot.reply_to(message, 'Введите заголовок заметки:')
    bot.register_next_step_handler(msg, process_note_title)

def process_note_title(message):
    user_id = message.from_user.id
    title = message.text
    msg = bot.reply_to(message, 'Введите содержание заметки:')
    bot.register_next_step_handler(msg, lambda m: process_note_content(m, user_id, title)) # m - новое сообщение пользователя (а точнее его ответ)

def process_note_content(message, user_id, title):
    content = message.text # извлекает содержание заметки, отправленное пользователем
    note_id = notes_manager.add_note_logic(user_id, title, content)
    bot.reply_to(message, f'Заметка "{title}" добавлена с ID: {note_id}')

# /show показывает все заметки пользователя
@bot.message_handler(commands=['show'])
def show_note(message):
    user_id = message.from_user.id
    notes = notes_manager.get_notes_logic(user_id)
    
    if not notes:
        bot.reply_to(message, 'У вас пока нет заметок.')
        return

    response_text = 'Ваши заметки:\n\n'
    for note in notes:
        note_id, title, content, created_at = note # Здесь идет распаковка кортежей, ведь каждая строка из note является кортежем вида (id, title, content, created_at)
        response_text += f'ID: {note_id}\nЗаголовок: {title}\nСодержание: {content}\nДата создания: {created_at}\n\n'

    bot.reply_to(message, response_text)

# /delete осуществляет удаление заметки по ID
@bot.message_handler(commands=['delete'])
def delete_note_command(message):
    user_id = message.from_user.id
    msg = bot.reply_to(message, 'Введите ID заметки, которую хотите удалить:')
    bot.register_next_step_handler(msg, lambda m: process_delete_note(m, user_id))

def process_delete_note(message, user_id):
    try:
        note_id = int(message.text)
        notes_manager.delete_note_logic(user_id, note_id)
        bot.reply_to(message, f'Заметка с ID {note_id} удалена.')
    except ValueError:
        bot.reply_to(message, 'Пожалуйста, введите корректный ID заметки (число).')

#  /clear удаляет все заметки с подтверждением
@bot.message_handler(commands=['clear'])
def delete_all_notes(message):
    user_id = message.from_user.id
    bot.reply_to(message, 'Для подтверждения удаления всех заметок, пожалуйста, нажмите кнопку ниже.', reply_markup=notes_manager.get_clear_confirmation_markup())

# Обработчик нажатий на inline-кнопки
@bot.callback_query_handler(func=lambda call: True)
def control(call):
    # Отвечаем на callback, чтобы убрать долгую загрузку у кнопки в интерфейсе Telegram
    bot.answer_callback_query(call.id)

    # Проверяем, какая кнопка была нажата, по значению callback_data
    if call.data == 'cancel_action':
        # Если пользователь нажал кнопку "Отмена" при подтверждении удаления
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Действие отменено', reply_markup=None)

    elif call.data == 'confirm_clear':
        # Подтверждение удаления всех заметок с защитой от случайного нажатия
        user_id = call.message.chat.id
        # Создаём атрибут функции, чтобы хранить счётчик попыток для каждого пользователя
        if not hasattr(delete_all_notes, 'attempt_count'): # Инвертируем результат в сторону True, если атрибута нет, с помощью not
            # hasattr(delete_all_notes, 'attempt_count') проверяет, есть ли у функции delete_all_notes атрибут с именем attempt_count
            delete_all_notes.attempt_count = {}

        # Если пользователь ещё не начинал подтверждение, создаём счётчик
        if user_id not in delete_all_notes.attempt_count:
            delete_all_notes.attempt_count[user_id] = 0

        # Проверяем, сколько раз пользователь уже нажал кнопку подтверждения
        if delete_all_notes.attempt_count[user_id] < 2:
            # Если нажал меньше 3 раз, увеличиваем счётчик и просим нажать ещё
            delete_all_notes.attempt_count[user_id] += 1
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Вы подтвердили удаление. Пожалуйста, нажмите кнопку еще {3 - delete_all_notes.attempt_count[user_id]}'
                                                                                                         f' раз(а) для подтверждения.', reply_markup=notes_manager.get_clear_confirmation_markup())
        else:
            # Если нажал 3 раза, удаляем все заметки пользователя
            notes_manager.delete_all_notes_logic(user_id)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Все заметки удалены!', reply_markup=None)

    elif call.data == 'confirm_clear_reminders':
        user_id = call.message.chat.id
        # Создаём атрибут функции, чтобы хранить счётчик попыток для каждого пользователя
        if not hasattr(delete_all_reminders_command, 'attempt_count'):
            delete_all_reminders_command.attempt_count = {}

        # Если пользователь ещё не начинал подтверждение, задаём счётчик
        if user_id not in delete_all_reminders_command.attempt_count:
            delete_all_reminders_command.attempt_count[user_id] = 0

        # Проверяем, сколько раз пользователь уже нажал кнопку подтверждения
        if delete_all_reminders_command.attempt_count[user_id] < 2:
            # Если нажал меньше 3 раз, увеличиваем счётчик и просим нажать ещё
            delete_all_reminders_command.attempt_count[user_id] += 1
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Вы подтвердили удаление. Пожалуйста, нажмите кнопку еще {3 - delete_all_reminders_command.attempt_count[user_id]} раз(а) для подтверждения.', reply_markup=get_clear_reminders_confirmation_markup())
        else:
            # Если нажал 3 раза, удаляем все напоминания пользователя
            count = delete_all_reminders_logic(user_id)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Все напоминания ({count} шт.) удалены!', reply_markup=None)

# /расписание открывает расписание ВГУ им. П.М. Машерова
@bot.message_handler(commands=['расписание', 'timetable'])
def send_timetable_link(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Открыть расписание', url='https://vsu.by/studentam/raspisanie-zanyatij.html  ')
    markup.add(btn)
    bot.reply_to(message, "Нажмите кнопку ниже, чтобы открыть расписание:", reply_markup=markup)

# Обработчик сообщений с текстом "help", "помощь", "gjvjom" используется также для справки без "/"
@bot.message_handler(regexp='[Hh]elp|[Пп]омощь|[Gg]jvjom')
def send_help_regex(message):
    bot.reply_to(message, "<b>Бот предназначен для создания Заметок.</b>", parse_mode="html")

#  /remind для установки напоминания
@bot.message_handler(commands=['remind'])
def set_reminder_command(message):
    # Показываем пользователю его заметки
    user_id = message.from_user.id
    notes = notes_manager.get_notes_logic(user_id)

    if not notes:
        bot.reply_to(message, 'У вас нет заметок, к которым можно добавить напоминание.')
        return

    # Формируем список заметок
    response_text = 'Выберите ID заметки, для которой хотите установить напоминание:\n\n'
    for note in notes:
        note_id, title, content, created_at = note
        response_text += f'ID: {note_id} | Заголовок: {title}\n'

    response_text += '\nВведите ID заметки:'
    msg = bot.reply_to(message, response_text)
    bot.register_next_step_handler(msg, lambda m: ask_reminder_time(m, user_id))

def ask_reminder_time(message, user_id):
    try:
        note_id = int(message.text)
        # Проверим, что заметка существует
        notes = notes_manager.get_notes_logic(user_id)
        note_exists = any(note[0] == note_id for note in notes)
        if not note_exists:
            bot.reply_to(message, 'Заметка с таким ID не найдена.')
            return

        # Попросим ввести дату в новом формате
        msg = bot.reply_to(message, 'Введите дату и время напоминания в формате: DD.MM.YYYY HH:MM (например, 15.11.2025 18:30)')
        bot.register_next_step_handler(msg, lambda m: process_reminder_time(m, user_id, note_id))
    except ValueError:
        bot.reply_to(message, 'Пожалуйста, введите корректный ID заметки (число).')

def process_reminder_time(message, user_id, note_id):
    reminder_time_str = message.text.strip() #Извлекает текст из сообщения пользователя и удаляет лишние пробелы в начале и конце

    # Проверим формат даты (только до минут)
    try:
        # Попробуем распарсить дату и время до минут
        datetime.strptime(reminder_time_str, '%d.%m.%Y %H:%M') # пытается преобразовать строку в объект даты и времени
    except ValueError:
        bot.reply_to(message, 'Неверный формат даты. Используйте формат: DD.MM.YYYY HH:MM (например, 15.11.2025 18:30)')
        return

    # Добавим :00 к времени, чтобы учитывать секунды, ибо в базе данных время хранится с секундами
    full_reminder_time_str = reminder_time_str + ":00"

    # Получим заголовок заметки для сообщения
    notes = notes_manager.get_notes_logic(user_id)
    title = next((note[1] for note in notes if note[0] == note_id), "Без заголовка")

    # Добавим напоминание в БД
    reminder_message = f"Напоминание по заметке: {title}"
    add_reminder(user_id, note_id, full_reminder_time_str, reminder_message)

    bot.reply_to(message, f'Напоминание установлено на {reminder_time_str} для заметки с ID {note_id}.')

# /show_reminders показывает все напоминания пользователя
@bot.message_handler(commands=['show_reminders'])
def show_reminders_command(message):
    user_id = message.from_user.id
    reminders_list = get_user_reminders_logic(user_id)

    if not reminders_list:
        bot.reply_to(message, 'У вас нет активных напоминаний.')
        return

    response_text = 'Ваши активные напоминания:\n\n'
    for reminder in reminders_list:
        reminder_id, note_id, reminder_time, message_text, is_sent = reminder
        status = "отправлено" if is_sent else "ожидает"
        # Получаем заголовок заметки по её ID для формирования текста напоминания.
        # Если заметка с указанным ID не найдена, возвращается строка "Без заголовка".
        notes = get_notes_logic(user_id)
        note_title = next((note[1] for note in notes if note[0] == note_id), "Без заголовка") # note[1] — это заголовок заметки (второй элемент)
        # note[0] — это ID заметки (первый элемент)
        response_text += f'ID напоминания: {reminder_id}\nДля заметки: "{note_title}"\nВремя: {reminder_time}\nСтатус: {status}\nТекст: {message_text}\n\n'

    bot.reply_to(message, response_text)

# /delete_reminder удаляет напоминания по ID
@bot.message_handler(commands=['delete_reminder'])
def delete_reminder_command(message):
    user_id = message.from_user.id
    reminders_list = get_user_reminders_logic(user_id)

    if not reminders_list:
        bot.reply_to(message, 'У вас нет активных напоминаний для удаления.')
        return

    response_text = 'Ваши активные напоминания:\n\n'
    for reminder in reminders_list:
        reminder_id, note_id, reminder_time, message_text, is_sent = reminder
        status = "отправлено" if is_sent else "ожидает"
        # Получаем заголовок заметки, чтобы пользователь не путал ID напоминания и ID заметки
        notes = get_notes_logic(user_id)
        note_title = next((note[1] for note in notes if note[0] == note_id), "Без заголовка")
        response_text += f'ID напоминания: {reminder_id}\nДля заметки: "{note_title}"\nВремя: {reminder_time}\nСтатус: {status}\nТекст: {message_text}\n\n'

    response_text += '\nВведите ID напоминания, которое хотите удалить:'
    msg = bot.reply_to(message, response_text)
    bot.register_next_step_handler(msg, lambda m: process_delete_reminder(m, user_id))

def process_delete_reminder(message, user_id):
    try:
        reminder_id = int(message.text)
        success = delete_reminder_logic(reminder_id, user_id)

        if success:
            bot.reply_to(message, f'Напоминание с ID {reminder_id} удалено.')
        else:
            bot.reply_to(message, 'Напоминание с таким ID не найдено или не принадлежит вам.')
    except ValueError:
        bot.reply_to(message, 'Пожалуйста, введите корректный ID напоминания (число).')

# /clear_reminders удаляет все напоминаня с подтверждением
@bot.message_handler(commands=['clear_reminders'])
def delete_all_reminders_command(message):
    user_id = message.from_user.id
    # Проверим, есть ли у пользователя напоминания
    reminders_list = get_user_reminders_logic(user_id)

    if not reminders_list:
        bot.reply_to(message, 'У вас нет активных напоминаний для удаления.')
        return

    # Спрашиваем подтверждение
    markup = types.InlineKeyboardMarkup()
    btn_confirm = types.InlineKeyboardButton('Да, удалить все', callback_data='confirm_clear_reminders')
    btn_cancel = types.InlineKeyboardButton('Отмена', callback_data='cancel_action')
    markup.row(btn_confirm, btn_cancel)

    bot.reply_to(message, 'Вы уверены, что хотите удалить все свои напоминания?', reply_markup=markup)

# Обработчик всех остальных сообщений
@bot.message_handler()
def info(message):
    if message.text.lower() == 'привет':
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        if last_name:
            full_name = f'{first_name} {last_name}'
        else:
            full_name = f'{first_name}'

        bot.send_message(message.chat.id, f'Привет, {full_name}!')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')

if __name__ == '__main__':
    print("Бот запущен...")
    reminders.start_reminder_thread()
    bot.infinity_polling()