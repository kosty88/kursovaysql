import random

import psycopg2

from creatdb import createdb


from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup


print('Start telegram bot...')
count_list = [1]         # счетчик 10 бесплатных слов

state_storage = StateMemoryStorage()
token_bot = 'YOU_TOKEN'
bot = TeleBot(token_bot, state_storage=state_storage)

conn = psycopg2.connect(database="kursovay", user="postgres", password="PostgreS")
with conn.cursor() as cur:
    cur.execute(
        """
        DROP TABLE common_words;
        DROP TABLE personal_words;
        DROP TABLE users;
        """
    )

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    user_id SERIAL PRIMARY KEY,
    activate BOOLEAN NOT NULL,
    username INTEGER);
    """)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS personal_words (
            id SERIAL PRIMARY KEY ,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            russian TEXT NOT NULL,
            english TEXT NOT NULL
        );
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS common_words (
            id SERIAL PRIMARY KEY,
            word_id INTEGER REFERENCES personal_words(id) ON DELETE CASCADE,
            english TEXT NOT NULL
        );
    """
    )
    conn.commit()
known_users = []
userStep = {}
buttons = []

def create_russian(message):
    path = message.text
    for char in path:
        code = ord(char)
        if not (
            (1040 <= code <= 1071) or
            (1072 <= code <= 1103) or
            code == 1025 or code == 1105):
            bot.send_message(message.chat.id, 'В слове есть не русские символы')
            return False
    print("Слово русское")

    msg_eng = bot.send_message(message.chat.id, 'Введите английское слово: ')
    bot.register_next_step_handler(msg_eng, create_english, path)
    return path


def create_english(message, path):
    path_eng = message.text
    for char in path_eng:
        code = ord(char)
        if not (
                (65 <= code <= 90) or
                (97 <= code <= 122)
        ):
            bot.send_message(message.chat.id, 'В слове есть не английские символы')
            return False
    print("Слово английское")

    msg_eng = bot.send_message(message.chat.id, 'Введите 4 английских слова для выбора')
    bot.register_next_step_handler(msg_eng, add_words, path, path_eng)


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    count = max(count_list)
    cid = message.chat.id
    user_id = message.from_user.id
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (username,activate) VALUES (%s, %s);
                    """, (user_id, False))
        conn.commit()
        createdb(conn)

    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, f"""👋 {message.from_user.first_name}, давай попрактикуемся в английском языке. Тренировки можешь проходить в удобном для себя темпе.
    У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения. Для этого воспрользуйся инструментами:
    * добавить слово ➕,
    * удалить слово 🔙.
    Ну что, начнём ⬇️.""")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT russian FROM personal_words WHERE id=%s;
            """, (count,))
        translate = cur.fetchone()[0]

        cur.execute("""
            SELECT english FROM personal_words WHERE id=%s;
            """, (count,))
        target_word = cur.fetchone()[0]

        cur.execute("""
            SELECT english FROM common_words WHERE word_id=%s;
            """, (count,))
        low = cur.fetchmany(4)              # список кортежей дополнительных 4 слов
        others = []                          # пустой список дополн слов
        for i in low:
            for k in i:
                others.append(k)             # добавление в пустой список слов из БД

    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others
    bot.register_next_step_handler(message, message_reply)


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    with conn.cursor() as cur:
        cur.execute("""
            select COUNT(russian) FROM personal_words;
            """, )
        len_count = cur.fetchone()[0]
    if len(count_list) <= len_count:
        maxim = max(count_list) + 1
        # print(maxim)
        count_list.append((maxim))
        markup = types.ReplyKeyboardMarkup(row_width=2)

        global buttons
        buttons = []
        with conn.cursor() as cur:
            cur.execute("""
                    SELECT russian FROM personal_words WHERE id=%s;
                    """, (maxim,))
            translate = cur.fetchone()[0]

            cur.execute("""
                    SELECT english FROM personal_words WHERE id=%s;
                    """, (maxim,))
            target_word = cur.fetchone()[0]

            cur.execute("""
                    SELECT english FROM common_words WHERE word_id=%s;
                    """, (maxim,))
            low = cur.fetchmany(4)  # список кортежей дополнительных 4 слов
            others = []  # пустой список дополн слов
            for i in low:
                for k in i:
                    others.append(k)  # добавление в пустой список слов из БД

        target_word_btn = types.KeyboardButton(target_word)
        buttons.append(target_word_btn)
        other_words_btns = [types.KeyboardButton(word) for word in others]
        buttons.extend(other_words_btns)
        random.shuffle(buttons)
        markup.add(*buttons)

        greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
        bot.send_message(message.chat.id, greeting, reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word
            data['translate_word'] = translate
            data['other_words'] = others

    else:
        name = message.from_user.first_name
        greeting = f"Бесплатные слова для {name} закончились, активируйте подписку!"
        bot.send_message(message.chat.id, greeting)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        del_word =data['translate_word']

    with conn.cursor() as cur:
        cur.execute("""
                DELETE FROM personal_words WHERE russian=%s;
                """, (del_word,))
        conn.commit()
        cur.execute("""
                select COUNT(russian) FROM personal_words;
                """, )
        word_count = cur.fetchone()[0]
    greeting = f"Слово {del_word} успешно удалено!"
    bot.send_message(message.chat.id, greeting)

    bot.send_message(message.chat.id, f'Осталовь {word_count} слов для изучения')


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    msg = bot.send_message(cid, 'Введите русское слово: ')
    bot.register_next_step_handler(msg, create_russian)


def add_words(message, path, path_eng):
    path_eng_other = message.text
    s = path_eng_other.replace(",", '')
    word_list = s.split()
    with conn.cursor() as cur:
        user_id = message.from_user.id
        cur.execute("""
                    SELECT user_id FROM users WHERE username=%s;
                """, (user_id,))
        user_id_add = cur.fetchone()[0]

        cur.execute("""
                INSERT INTO personal_words (user_id,russian,english) VALUES (%s, %s, %s);
                        """, (user_id_add, path, path_eng))
        conn.commit()

        cur.execute("""
                    SELECT id FROM personal_words WHERE russian=%s;
                    """, (path,))
        rus_id = cur.fetchone()[0]

        for vali in word_list:
            cur.execute("""
                    INSERT INTO common_words (word_id, english) VALUES (%s, %s);
                            """, (rus_id, vali))
        conn.commit()
        bot.send_message(message.chat.id, f'Слово {path} успешно добавлено')

        cur.execute("""
                    select COUNT(russian) FROM personal_words;
                    """, )
        word_count = cur.fetchone()[0]
        bot.send_message(message.chat.id, f'Осталовь {word_count} слов для изучения')




@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
            bot.register_next_step_handler(message)

        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)
