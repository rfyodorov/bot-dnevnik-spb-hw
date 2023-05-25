import telebot
import json
import logging
from parser import run_parser, run_parser_wallet, run_parser_teacher
from telebot import types


def run_bot(conf_vars: dict) -> None:
    # logger = telebot.logger
    # telebot.logger.setLevel(logging.INFO)
    logging.basicConfig(encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s',
                        datefmt='%Y%m%d %H:%M:%S')

    help_message = '''
    Список доступных команд:
    /today  - домашнее задание на сегодня
    /tommorow - домашнее задание на завтра
    /tommorow2 - домашнее задание на послезавтра
    /date 2023-05-18 - домашнее задание за 2023-05-18
    /buttons - показать кнопки (inline)
    /keyboard - показать быструю клавиатуру
    /wallet - показать баланс школьного кошелька
    /teachers - показать ФИО учителей
    /auth ***** - зарегистрироваться по паролю
    '''
    auth_message = '''
    Для начала работы с ботом пришлите пароль:
    /auth *****
    '''

    bot = telebot.TeleBot(conf_vars['tbot_token'])
    chat_pass = conf_vars['chat_pass']

    # вспомогательная функция, возвращает первый переданный аргумент
    def extract_arg(arg) -> str:
        try:
            first_arg = arg.split()[1:][0]
        except IndexError:
            first_arg = 'arg is null'
        return first_arg

    # вспомогательная функция, чтение словаря разрешенных пользователей из файла
    def load_data() -> dict:
        with open("users.json", "r") as users_file:
            users = json.load(users_file)
        return users

    # вспомогательная функция, добавление нового пользователя в список разрешенных
    def save_data(data) -> None:
        users = load_data()
        users[data] = "yes"
        with open("users.json", "w") as users_file:
            json.dump(users, users_file)
        logging.info('Запись в файл users.json')

    # Аутентификация. Для начала общения с ботом, требуется выполнить команду: auth <pass>
    @bot.message_handler(commands=['auth'])
    def command_auth(message) -> None:
        users_list = load_data()

        if str(message.chat.id) in users_list.keys():
            bot.send_message(message.chat.id, "Мы уже знакомы")
        else:
            client_pass = extract_arg(message.text)
            if client_pass == chat_pass:
                save_data(message.chat.id)
                bot.send_message(message.chat.id, "Вы зарегистрированы")
                bot.send_message(message.chat.id, help_message)
            else:
                bot.send_message(message.chat.id, "Введите правильный пароль")

    # Авторизация пользователя, используется в виде декоратора
    def check_access(f):
        def wrapper(message):
            logging.debug(f'Проверка пользователя {message.chat.id}')
            users_list = load_data()
            if str(message.chat.id) in users_list.keys():
                logging.info(f'Авторизация пройдена. Запрос от пользователя {message.chat.id}:')
                f(message)
            else:
                logging.debug(f'Пользователь {message.chat.id} не найден в users.json')
                bot.send_message(message.chat.id, 'Требуется авторизация')
                bot.send_message(message.chat.id, auth_message)

        return wrapper

    # Начинаем с отправки help_message пользователю
    @bot.message_handler(commands=['start'])
    @check_access
    def start_tasks(message):
        bot.send_message(message.chat.id, help_message)

    # ДЗ на сегодня
    @bot.message_handler(commands=['today'])
    @check_access
    def task_today(message):
        answer = run_parser()
        logging.debug(f'commands=today\n {answer}')
        bot.send_message(message.chat.id, answer, parse_mode='HTML')

    # ДЗ на завтра
    @bot.message_handler(commands=['tommorow'])
    @check_access
    def task_tommorow(message):
        answer = run_parser('tommorow')
        logging.debug(f'commands=tommorow\n {answer}')
        bot.send_message(message.chat.id, answer, parse_mode='HTML')

    # ДЗ на послезавтра
    @bot.message_handler(commands=['tommorow2'])
    @check_access
    def task_tommorow2(message):
        answer = run_parser('tommorow2')
        logging.debug(f'commands=tommorow2\n {answer}')
        bot.send_message(message.chat.id, answer, parse_mode='HTML')

    # Отправляем уроки заданные в определенную дату ГГГГ-ММ-ДД
    @bot.message_handler(commands=['date'])
    @check_access
    def task_date(message):
        set_day = extract_arg(message.text)
        logging.info(f'Задан день: {set_day}')
        answer = run_parser(set_day)
        bot.send_message(message.chat.id, answer, parse_mode='HTML')

    # Узнаем баланс кошелька
    @bot.message_handler(commands=['wallet'])
    @check_access
    def task_wallet(message):
        answer = run_parser_wallet()
        logging.debug(f'commands=wallet\n {answer}')
        bot.send_message(message.chat.id, answer, parse_mode='HTML')

    # Узнаем ФИО преподаватлей
    @bot.message_handler(commands=['teachers'])
    @check_access
    def task_teacher(message):
        answer = run_parser_teacher()
        logging.debug(f'commands=teachers\n {answer}')
        bot.send_message(message.chat.id, answer, parse_mode='HTML')

    # Показываем кнопки (Inline клавиатура)
    @bot.message_handler(commands=['buttons'])
    @check_access
    def buttons_tasks(message):
        logging.debug(f'показана InlineKeyboardMarkup')
        inline_keyboard = telebot.types.InlineKeyboardMarkup()
        button1 = telebot.types.InlineKeyboardButton(text="на сегодня", callback_data="today")
        button2 = telebot.types.InlineKeyboardButton(text="на завтра", callback_data="tommorow")
        button3 = telebot.types.InlineKeyboardButton(text="на послезавтра", callback_data="tommorow2")
        inline_keyboard.row(button1, button2, button3)
        bot.send_message(message.from_user.id, "Показать домашнее задание:",  reply_markup=inline_keyboard)

    # Показываем клавиатуру (основная)
    @bot.message_handler(commands=['keyboard'])
    @check_access
    def keyboard1(message):
        logging.debug(f'включена ReplyKeyboardMarkup')
        reply_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_keyboard.row('на сегодня', 'на завтра', 'на послезавтра')
        reply_keyboard.add(types.KeyboardButton("полезная информация"))
        bot.send_message(message.chat.id, "Показать домашнее задание:", reply_markup=reply_keyboard)

    # Показываем клавиатуру (полезная информация)
    @bot.message_handler(commands=['keyboard2'])
    @check_access
    def keyboard2(message):
        logging.debug(f'включена ReplyKeyboardMarkup')
        reply_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_keyboard.row('кошелёк', 'учителя', 'справка')
        reply_keyboard.add(types.KeyboardButton("назад"))
        bot.send_message(message.chat.id, "Полезная информация:", reply_markup=reply_keyboard)

    # обработка callback от InlineKeyboard
    @bot.callback_query_handler(func=lambda call: True)
    def callback_function1(callback_obj: telebot.types.CallbackQuery):
        if callback_obj.data == "today":
            answer = run_parser('today')
            logging.debug(f'кнопка=на сегодня\n {answer}')
            bot.send_message(callback_obj.from_user.id,  answer, parse_mode='HTML')
        elif callback_obj.data == "tommorow":
            answer = run_parser('tommorow')
            logging.debug(f'кнопка=на завтра\n {answer}')
            bot.send_message(callback_obj.from_user.id,  answer, parse_mode='HTML')
        elif callback_obj.data == "tommorow2":
            answer = run_parser('tommorow2')
            logging.debug(f'кнопка=на послезавтра\n {answer}')
            bot.send_message(callback_obj.from_user.id,  answer, parse_mode='HTML')
        elif callback_obj.data == "help":
            logging.debug(f'кнопка=help\n')
            bot.send_message(callback_obj.from_user.id, help_message)
        elif callback_obj.data == "wallet":
            answer = run_parser_wallet()
            logging.debug(f'кнопка=на кошелек\n {answer}')
            bot.send_message(callback_obj.from_user.id,  answer, parse_mode='HTML')
        elif callback_obj.data == "teachers":
            answer = run_parser('tommorow2')
            logging.debug(f'кнопка=преподаватели\n {answer}')
            bot.send_message(callback_obj.from_user.id,  answer, parse_mode='HTML')
        bot.answer_callback_query(callback_query_id=callback_obj.id)

    # обработка текстовых запросов от ReplyKeyboard
    @bot.message_handler(content_types=['text'])
    @check_access
    def message_reply(message):
        if message.text == "на сегодня":
            task_today(message)
        if message.text == "на завтра":
            task_tommorow(message)
        if message.text == "на послезавтра":
            task_tommorow2(message)
        if message.text == "полезная информация":
            old_keyboard = telebot.types.ReplyKeyboardRemove()
            bot.send_message(message.from_user.id, 'Переход в раздел', reply_markup=old_keyboard)
            keyboard2(message)
        if message.text == "кошелёк":
            task_wallet(message)
        if message.text == "учителя":
            task_teacher(message)
        if message.text == "назад":
            old_keyboard = telebot.types.ReplyKeyboardRemove()
            bot.send_message(message.from_user.id, 'Переход в раздел', reply_markup=old_keyboard)
            keyboard1(message)
        if message.text == "справка":
            bot.send_message(message.from_user.id, help_message)

    bot.polling(non_stop=True)
