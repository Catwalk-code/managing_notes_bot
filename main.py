from telebot import types
import webbrowser
from config import bot

import notes_manager
import reminders   # Импортируем файл с обработчиками напоминаний (пока что он пуст)

# Переносим оставшиеся обработчики, которые не попали в notes_manager

@bot.message_handler(commands=['расписание', 'timetable'])
def site(message):
    webbrowser.open_new_tab("https://vsu.by/studentam/raspisanie-zanyatij.html  ")


@bot.message_handler(regexp='[Hh]elp|[Пп]омощь|[Gg]jvjom')
def send_help_regex(message):
    bot.reply_to(message, "<b>Бот предназначен для создания Заметок.</b>", parse_mode="html")


@bot.message_handler(content_types=['photo'])
def get_photo(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Перейти на сайт', url='https://vsu.by/studentam/raspisanie-zanyatij.html  ')
    markup.row(btn1)
    btn2 = types.InlineKeyboardButton('Удалить фото', callback_data='delete')
    btn3 = types.InlineKeyboardButton('Изменить фото', callback_data='edit')
    markup.row(btn2, btn3)
    bot.reply_to(message, 'Какое красивое фото!', reply_markup=markup)

@bot.message_handler(regexp='[Hh]elp|[Пп]омощь|[Gg]jvjom')
def send_help_regex(message):
    bot.reply_to(message, "<b>Бот предназначен для создания Заметок.</b>", parse_mode="html")

# Эти обработчики нужно будет переместить в notes_manager или reminders, когда там появится логика
@bot.callback_query_handler(func=lambda call: call.data == 'delete')
def handle_delete_callback(call):
    # Удалить фото (или заметку, если кнопка связана с заметкой)
    bot.answer_callback_query(call.id) # Отвечаем на callback
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Фото (или заметка) удалена!", reply_markup=None)

@bot.callback_query_handler(func=lambda call: call.data == 'edit')
def handle_edit_callback(call):
    # Начать редактирование (или заметки)
    bot.answer_callback_query(call.id)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Начинаем редактирование...", reply_markup=None)

# Обработчик общих сообщений
'''Это правило перехватывает абсолютно сообщения, которые не подходят под другие обработчики. Его важно опустить в самый низ, 
чтобы другие команды срабатывали корректно
Все команды кроме этих должны быть добавлены до этого обработчика.'''
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

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()