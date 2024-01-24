# -*- coding: utf-8 -*-
import psycopg2
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InputMediaPhoto
import requests

import config

text = ''
type = ''
caption = ''
id = ''
msg = ''
user_id = ''
check = 0
conn = psycopg2.connect(
    host=config.PGHOST,
    database=config.PGDATABASE,
    user=config.PGUSER,
    port=config.PGPORT,
    password=config.PGPASS)

cursor = conn.cursor()

ADMIN = 'cryptobroker_x'
ADMIN_ID = '6599410167'
TOKEN = '6973189726:AAEwiaeNnRRWKuu468BVKL0BLgbhhYCrq3k'


bot = telebot.TeleBot(TOKEN)

###################### СООБЩЕНИЕ ПОСЛЕ ПОДАЧИ ЗАЯВКИ ######################

@bot.chat_join_request_handler()
def new_start(message: telebot.types.ChatJoinRequest):
    btn1 = InlineKeyboardButton(text= "Задать вопрос о консультации", url='https://t.me/valeriya_astropsy')
    btn2 = InlineKeyboardButton(text = "Получить авторскую медитацию", callback_data='author')
    btn3 = InlineKeyboardButton(text = "Перейти в канал VALERIYA LAGUZ ✨", url='https://t.me/+UKluJYX3STYzMzJi')
    keyboard = InlineKeyboardMarkup().add(btn1).add(btn2).add(btn3)

    photo = open('start.jpg', 'rb')
    bot.send_photo(message.from_user.id, photo=photo, caption=f"🔴LIVE: 20.01.24 в 14:00 UTC+3\n\nНЕ ПРОПУСТИТЕ СЛЕДУЮЩИЙ ЭФИР, ведь это прекрасная возможность задать свой первый вопрос картам таро!\n\nС помощью кнопок ниже Вы можете записаться на консультацию уже сейчас или получить мою авторскую медитацию в подарок 🎁\n\n*Что Вас интересует?*", reply_markup = keyboard)
    
    bot.approve_chat_join_request(message.chat.id, message.from_user.id)

    cursor.execute(f"""SELECT user_id FROM Users WHERE user_id=:user""",  {'user': message.from_user.id})
    username = cursor.fetchone()
    conn.commit()
    
    if username is None:
        cursor.execute('INSERT INTO Users (user_id, name, username) VALUES (?, ?, ?)', (message.from_user.id, f'{message.from_user.first_name} {message.from_user.last_name}', message.from_user.username))
        conn.commit()




###################### БЛОК РАССЫЛКИ ######################

@bot.message_handler(commands = ['send'])

def msg_sends(message):
    if message.from_user.username == ADMIN:
        btn1 = KeyboardButton("Текст")
        btn2 = KeyboardButton("Фото")
        btn3 = KeyboardButton("Голосовое")
        btn5 = KeyboardButton("Отмена")
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(btn1).add(btn2).add(btn3).add(btn5)
        bot.send_message(message.from_user.id, 'Выберите тип отправляемого медиа:', parse_mode= 'Markdown', reply_markup = keyboard)
        bot.register_next_step_handler(message, upload_send)
    else:
        bot.send_message(message.from_user.id, f'Вы не админ')

def upload_send(message):

    if message.text == 'Фото':
        bot.send_message(message.from_user.id, 'Пришлите фото, можно с описанием', parse_mode= 'Markdown')
        bot.register_next_step_handler(message, photo)
    elif message.text == "Текст":
        bot.send_message(message.from_user.id, 'Пришлите текст', parse_mode= 'Markdown')
        bot.register_next_step_handler(message, text_msg)
    elif message.text == 'Голосовое':
        bot.send_message(message.from_user.id, 'Пришлите голосовое сообщение', parse_mode= 'Markdown')
        bot.register_next_step_handler(message, voice)
    else:
        msg_send(message)

def text_msg(message):
    """Функция отправки текста"""

    global type, text
    type = 'text'
    text = message.text

    btn1 = KeyboardButton('Да')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(btn1)

    bot.send_message(message.from_user.id, f"Подтвердите отправку сообщения всем подписчикам: \n\nОтсылаем: {type}", parse_mode= 'Markdown', reply_markup = keyboard)
    bot.register_next_step_handler(message, sender)

def photo(message):
    """Функция отправки фото"""

    global type, caption
    type = 'photo'
    caption = message.caption

    fileID = message.photo[-1].file_id   
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("image.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)

    btn1 = KeyboardButton('Да')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(btn1)

    bot.send_message(message.from_user.id, f"Подтвердите отправку сообщения всем подписчикам: \n\nОтсылаем: {type}", parse_mode= 'Markdown', reply_markup = keyboard)
    bot.register_next_step_handler(message, sender)

def voice(message):
    """Функция отправки гс"""

    global type
    type = 'voice'

    file_info = bot.get_file(message.voice.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))

    with open('voice.ogg','wb') as f:
        f.write(file.content)

    btn1 = KeyboardButton('Да')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(btn1)

    bot.send_message(message.from_user.id, f"Подтвердите отправку сообщения всем подписчикам: \n\nОтсылаем: {type}", parse_mode= 'Markdown', reply_markup = keyboard)
    bot.register_next_step_handler(message, sender)


def sender(message):
    global text, type, caption, id

    if message.text == 'Да':
        cursor.execute(f"""SELECT user_id FROM Users""")
        all_ids = cursor.fetchall()

        count = 0

        try:
            for id in all_ids:
                if id[0]:
                    try:      
                        if type == 'photo':
                            new_file = open('image.jpg', 'rb')
                            bot.send_photo(id[0], photo=new_file, caption=caption, parse_mode='html')
                        elif type == 'voice':
                            f = open('voice.ogg', 'rb')
                            bot.send_voice(id[0], f)
                        elif type == 'text':
                            bot.send_message(id[0], text, parse_mode='html')
                        count += 1
                    except:
                        pass
        except Exception as e:
            print(e)

        bot.send_message(message.from_user.id, f'Рассылка успешна закончена, всего получателей: {count}', parse_mode= 'Markdown')
        msg_send(message)
    else:
        bot.send_message(message.from_user.id, f'Рассылка отменена.')




###################### ГЛАВНОЕ МЕНЮ (/start) ######################

@bot.message_handler(commands = ['start'])
def msg_send(message):
    btn1 = KeyboardButton("👩‍💼 Нужна помощь?")
    btn2 = KeyboardButton("📋 Обо мне")
    btn3 = KeyboardButton("✍️ Предзапись на новый поток обучения таро Уейта")
    btn4 = KeyboardButton("🎞Приобрести мои курсы в записи")
    btn5 = KeyboardButton("💁‍♀️ Отзывы о моей работе")
    btn6 = KeyboardButton("🎁 Подписаться на получение скидок от Valeriya LAGUZ")
    btn7 = KeyboardButton("📲 Связаться со мной через удобный для вас мессенджер")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(btn1, btn2)
    keyboard.row(btn3)
    keyboard.row(btn4)
    keyboard.row(btn5)
    keyboard.row(btn6)
    keyboard.row(btn7)
    bot.send_message(message.from_user.id, 'Привет, меня зовут Валерия Laguz, раз в 2 недели я провожу эфир гаданий, где вы можете задать один вопрос, поэтому не забудьте подписаться на канал - ссылка в меню ниже.\n\nТакже с помощью кнопок внизу вы можете записаться на консультацию, получить мою авторскую медитацию и многое другое!\n\n*Что вас интересует?*', parse_mode= 'Markdown', reply_markup = keyboard)





###################### ОТВЕТЫ ПО КНОПКАМ (ТЕКСТ) ######################

@bot.message_handler(content_types='text')
def message_reply(message):

    global msg, user_id

    if message.text == "👩‍💼 Нужна помощь?":
        print('aaa')
        bot.send_message(message.from_user.id, "@valeriya_astropsy")

    if message.text == "📋 Обо мне":
        btn1 = InlineKeyboardButton(text= "Вам нужна помощь?", url='https://t.me/valeriya_astropsy')
        btn2 = InlineKeyboardButton(text = "Как работает Таро", callback_data='how_taro')
        btn3 = InlineKeyboardButton(text = "Узнать больше о ритуалах", callback_data='how_ritual')
        btn4 = InlineKeyboardButton(text = "Полный список моих услуг", callback_data='services')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2).add(btn3).add(btn4)

        photo = open('diplom.png', 'rb')
        bot.send_photo(message.from_user.id, photo=photo, caption="Здравствуйте, Меня зовут Валерия!\n\nЯ - дипломированный психолог и гипнолог, который практикует работу с картами таро и астро-психологию.\n\nЭти прекрасные инструменты помогают мне не только заглянуть в будущее, но и экологично выявить проблемы, мешающие вам жить прекрасной жизнью, которую вы безусловно заслуживаете.\n\nЯ уверенна, что мой метод более глубокий чем классический психоанализ, он дает более быстрые результаты, так как мы «копаем» с разных сторон. Мой подход позволяет быстро выявить первопричину и сразу же преступить к терапии. Например, если человек приходит к психологу, а на нем есть негативное воздействие, то классическая психология в этом случае не поможет.\n\nКаждый практикующий эксперт в чём-то более силен, в чём-то менее. Моя же главная сила заключается в том, чтобы изменять ситуацию в нужное русло. Для этого я использую руническую магию и другие ритуалы.", reply_markup=keyboard)


    if message.text == "✍️ Предзапись на новый поток обучения таро Уейта":
        btn1 = InlineKeyboardButton(text= "Предзапись подтверждаю ☑️", callback_data='okpotok')
        btn2 = InlineKeyboardButton(text = "Содержание курса", callback_data='courses')
        btn3 = InlineKeyboardButton(text = "Отзывы учеников", callback_data='fb_students')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2).add(btn3)

        user_id = message.from_user
        msg = bot.send_message(message.from_user.id, "Провожу предзапись на новый поток обучения базовому таро Райдера Уэйта\n\nОбучение стартует, когда наберётся группа.\n\nОриентировочный старт обучения: Январь 2024 года;\n\nСтоимость обучения: 20.000 рублей \n\nТе, кто вносят предоплату до начала потока, получают скидку 10%. Рассрочка также есть. Жду всех!\n\nЕсли у вас есть любые вопросы, просто напишите сюда: @valeriya_astropsy", reply_markup=keyboard)

    if message.text == "🎞Приобрести мои курсы в записи":
        btn1 = InlineKeyboardButton(text= "Таро", callback_data='taro')
        btn2 = InlineKeyboardButton(text = "Руны", callback_data='runi')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2)
    
        bot.send_message(message.from_user.id, "Сейчас вам доступны 2 актуальных курса: Таро для новичков и Руническая магия\n\nС чего вы хотели бы начать?", reply_markup=keyboard)

    if message.text == "💁‍♀️ Отзывы о моей работе":
        btn1 = InlineKeyboardButton(text= "Узнать стоимость", url='https://t.me/valeriya_astropsy')
        # btn2 = InlineKeyboardButton(text = "Полный список моих услуг", callback_data='services')
        keyboard = InlineKeyboardMarkup().add(btn1)
    
        bot.send_media_group(message.from_user.id, [InputMediaPhoto(open('1.png', 'rb'), ), InputMediaPhoto(open('2.png', 'rb')), InputMediaPhoto(open('3.png', 'rb')), InputMediaPhoto(open('4.png', 'rb')), InputMediaPhoto(open('5.png', 'rb')), InputMediaPhoto(open('6.png', 'rb')), InputMediaPhoto(open('7.png', 'rb'))])
        bot.send_message(message.from_user.id, "На скриншотах отзывы учеников по работе с Таро и о результатах рунической магии☝️\n\nЯ принимаю на консультацию через личные сообщения: @valeriya_astropsy\n\nКакие услуги я предлагаю:\n\n- Диагностика и проработка психологического состояния с помощью Метафорических ассоциативных карт (МАК);\n- Астро-психологический разбор вашего запроса;\n- Ответы на вопросы с помощью карт Таро;\n- Астро-психологический прогноз на год (Годовой соляр);\n- Определение предназначения с помощью натальной карты;\n- Релокация натальной карты;\n- Гипноз;\n- Диагностика негатива;\n- Магическая работа (чистки и гармонизации).", reply_markup=keyboard)


    if message.text == "🎁 Подписаться на получение скидок от Valeriya LAGUZ":
        btn1 = InlineKeyboardButton(text= "Хочу ☑️", callback_data='okskidka')
        btn2 = InlineKeyboardButton(text = "Записаться на консультацию", url='https://t.me/valeriya_astropsy')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2)
    
        user_id = message.from_user
        msg = bot.send_message(message.from_user.id, "Вы хотите получать актуальную информацию о всех новых скидках и бонусах?🎁", reply_markup=keyboard)

    if message.text == "📲 Связаться со мной через удобный для вас мессенджер":
        btn2 = InlineKeyboardButton(text = "Telegram", url='https://t.me/valeriya_astropsy')
        btn3 = InlineKeyboardButton(text = "WhatsApp", url='https://api.whatsapp.com/send/?phone=380636796997&text&type=phone_number&app_absent=0')
        keyboard = InlineKeyboardMarkup().add(btn2).add(btn3)

        bot.send_message(message.from_user.id, "Выберете мессенджер, в котором хотели бы связаться со мной:", reply_markup=keyboard)





###################### ОТВЕТЫ ПО КНОПКАМ (CALLBACK) ######################


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    global msg, user_id, check

    if call.data == "author":
        bot.send_audio(chat_id=call.message.chat.id, audio=open('audio.mp3', 'rb'), performer="Медитация Валерии Таролога")

    if call.data == "how_taro":
        bot.send_audio(chat_id=call.message.chat.id, caption="Рассказала подробно в голосовом сообщении. Нажмите, чтобы прослушать▶️", audio=open('audi.ogg', 'rb'), performer="Валерия Таролог", title="Как работает Таро")

    if call.data == "how_ritual":
        bot.send_audio(chat_id=call.message.chat.id, caption="Рассказала подробно в голосовом сообщении. Нажмите, чтобы прослушать▶️", audio=open('audio_2024-01-16_20-17-50.ogg', 'rb'), performer="Валерия Таролог", title="Больше о ритуалах")

    if call.data == "okpotok":
        btn1 = InlineKeyboardButton(text= "Предзапись подтверждаю ✅", callback_data='load')
        btn2 = InlineKeyboardButton(text = "Содержание курса", callback_data='courses')
        btn3 = InlineKeyboardButton(text = "Отзывы учеников", callback_data='fb_students')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2).add(btn3)
    
        bot.edit_message_text(chat_id = call.message.chat.id, message_id = msg.message_id, text = "Провожу предзапись на новый поток обучения базовому таро Райдера Уэйта\n\nОбучение стартует, когда наберётся группа.\n\nОриентировочный старт обучения: Январь 2024 года;\n\nСтоимость обучения: 20.000 рублей \n\nТе, кто вносят предоплату до начала потока, получают скидку 10%. Рассрочка также есть. Жду всех!\n\nЕсли у вас есть любые вопросы, просто напишите сюда: @valeriya_astropsy", reply_markup=keyboard)
        bot.send_message(ADMIN_ID, f"Пользователь @{user_id.username} подтвердил предзапись")

    if call.data == "okskidka":
        btn1 = InlineKeyboardButton(text= "Хочу ✅", callback_data='taro')
        btn2 = InlineKeyboardButton(text = "Записаться на консультацию", url='https://t.me/valeriya_astropsy')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2)

        bot.edit_message_text(chat_id = call.message.chat.id, message_id = msg.message_id, text = "Вы хотите получать актуальную информацию о всех новых скидках и бонусах?🎁", reply_markup=keyboard)
        bot.send_message(ADMIN_ID, f"Пользователь @{user_id.username} подтвердил предзапись")

    if call.data == "services":
        btn1 = InlineKeyboardButton(text= "Узнать стоимость", url='https://t.me/valeriya_astropsy')
        btn2 = InlineKeyboardButton(text = "Отзывы", callback_data='feedback')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2)

        bot.send_message(call.message.chat.id, 'Принимаю на консультацию через личные сообщения: @valeriya_astropsy\nКакие услуги я предлагаю:\n\n- Диагностика и проработка психологического состояния с помощью Метафорических ассоциативных карт (МАК);\n- Астро-психологический разбор вашего запроса;\n- Ответы на вопросы с помощью карт Таро;\n- Астро-психологический прогноз на год (Годовой соляр);\n- Определение предназначения с помощью натальной карты;\n- Релокация натальной карты;\n- Гипноз;\n- Диагностика негатива;\n- Магическая работа (чистки и гармонизации).', reply_markup = keyboard)

    if call.data == "courses":
        btn1 = InlineKeyboardButton(text= "Предзапись подтверждаю ☑️", callback_data='okcourses')
        btn2 = InlineKeyboardButton(text = "Отзывы учеников", callback_data='fb_students')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2)

        msg = bot.send_message(call.message.chat.id, 'План обучения\n\n1. Введение - Таро как инструмент.\n2. Старшие арканы. Учимся читать первые триплеты. Обращаю внимание, что триплеты мы будем читать в группе на протяжении всего курса!\n3. Учимся делать расклады на старших арканах. Изучаем схемы и составляем расклады.\n4. Таро-нумерология. О чем расскажет дата рождения?\n5. Продолжаем расшифровку - 40 младших Арканов\n6. Итог обучения. Обзор колод. Рекомендации начинающим тарологам.\n\nИтого, мы с вами обучаемся полтора месяца. Поверьте, это небольшой срок для освоения Таро. Многие мои ученики говорят, что я отвечаю четко и по делу, без воды. Поэтому я для вас создаю такой курс, где все значения будут простыми, четкими и понятными даже новичку. Я люблю конкретику и умею доносить информацию простым языком 🙂\n\nПосле прохождения курса вы смело сможете приступить к раскладам в вопросах карьеры, отношений, научитесь определять архетипы людей, сможете составлять прогнозы будущего.\n\nВопросов здоровья и разбора ситуаций между жизнью и смертью в моем курсе не будет, так как данные вопросы требуют опыта и наработки. Столь серьёзные вопросы я не рекомендую смотреть на начальном этапе.\n\nОбучение будет проходить в телеграм канале, с моей обратной связью, домашними заданиями и общением друг с другом 😉\n\nВ среднем каждый урок будет длиться 40 минут.', parse_mode= 'Markdown', reply_markup = keyboard)

    if call.data == "okcourses":
        btn1 = InlineKeyboardButton(text= "Предзапись подтверждаю ✅", callback_data='load')
        btn2 = InlineKeyboardButton(text = "Отзывы учеников", callback_data='fb_students')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2)

        bot.edit_message_text(chat_id = call.message.chat.id, message_id = msg.message_id, text = 'План обучения\n\n1. Введение - Таро как инструмент.\n2. Старшие арканы. Учимся читать первые триплеты. Обращаю внимание, что триплеты мы будем читать в группе на протяжении всего курса!\n3. Учимся делать расклады на старших арканах. Изучаем схемы и составляем расклады.\n4. Таро-нумерология. О чем расскажет дата рождения?\n5. Продолжаем расшифровку - 40 младших Арканов\n6. Итог обучения. Обзор колод. Рекомендации начинающим тарологам.\n\nИтого, мы с вами обучаемся полтора месяца. Поверьте, это небольшой срок для освоения Таро. Многие мои ученики говорят, что я отвечаю четко и по делу, без воды. Поэтому я для вас создаю такой курс, где все значения будут простыми, четкими и понятными даже новичку. Я люблю конкретику и умею доносить информацию простым языком 🙂\n\nПосле прохождения курса вы смело сможете приступить к раскладам в вопросах карьеры, отношений, научитесь определять архетипы людей, сможете составлять прогнозы будущего.\n\nВопросов здоровья и разбора ситуаций между жизнью и смертью в моем курсе не будет, так как данные вопросы требуют опыта и наработки. Столь серьёзные вопросы я не рекомендую смотреть на начальном этапе.\n\nОбучение будет проходить в телеграм канале, с моей обратной связью, домашними заданиями и общением друг с другом 😉\n\nВ среднем каждый урок будет длиться 40 минут.', parse_mode= 'Markdown', reply_markup = keyboard)
        bot.send_message(ADMIN_ID, f"Пользователь @{user_id.username} подтвердил предзапись")

    if call.data == "fb_students":
        btn1 = InlineKeyboardButton(text= "Предзапись подтверждаю ☑️", callback_data='okfb')
        btn2 = InlineKeyboardButton(text = "План обучения", callback_data='courses')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2)

        bot.send_media_group(call.message.chat.id, [InputMediaPhoto(open('fb1.png', 'rb')), InputMediaPhoto(open('fb2.png', 'rb')), InputMediaPhoto(open('fb3.png', 'rb'))])
        msg = bot.send_message(call.message.chat.id, "На скриншотах отзывы учеников по курсу Таро и Рунической магии☝️", reply_markup=keyboard)

    if call.data == "okfb":
        btn1 = InlineKeyboardButton(text= "Предзапись подтверждаю ✅", callback_data='load')
        btn2 = InlineKeyboardButton(text = "План обучения", callback_data='courses')
        keyboard = InlineKeyboardMarkup().add(btn1).add(btn2)

        bot.edit_message_text(chat_id = call.message.chat.id, message_id = msg.message_id, text = "На скриншотах отзывы учеников по курсу Таро и Рунической магии☝️", reply_markup=keyboard)
        bot.send_message(ADMIN_ID, f"Пользователь @{user_id.username} подтвердил предзапись")

    if call.data == "taro":
        btn1 = InlineKeyboardButton(text = "Получить доступ", url='https://t.me/valeriya_astropsy')
        keyboard = InlineKeyboardMarkup().add(btn1)

        bot.send_message(call.message.chat.id, text="Курс по обучению Таро рассчитан на полтора месяца обучения и включает: введение в Таро как инструмент, изучение старших и младших арканов, а также освоение раскладов. В своих уроках я даю четкую и понятную информацию, пригодную даже для новичков. Фокусируюсь на конкретных и простых объяснениях. По завершении обучения вы сможете проводить расклады по вопросам карьеры, отношений, определять архетипы людей и составлять прогнозы будущего.\n\nПродолжительность: 22 урока, в среднем по 40 минут каждый.\n\nПереходите по кнопке ниже👇 и напишите мне ХОЧУ ПРОБНЫЙ УРОК ПО ТАРО\n_____________\n\nЦена полного доступа: 10.000 рублей", reply_markup=keyboard)


    if call.data == "runi":
        btn1 = InlineKeyboardButton(text = "Получить доступ", url='https://t.me/valeriya_astropsy')
        keyboard = InlineKeyboardMarkup().add(btn1)

        bot.send_message(call.message.chat.id, text="Курс по рунической магии включает в себя 12 уроков, начиная с введения в мир рун и заканчивая практическими ритуалами. Учебный план охватывает: чтение рун, руническую магию, диагностику негатива, использование свечей и трав, создание рабочего алтаря, защиту и виды защиты, этику в магии, и, наконец, практическое колдовство. Каждое занятие предоставляется в виде видео урока, который будет доступен вам в любое удобное время для изучения.\n\nСтудентам рекомендуется приобрести комплект скандинавских рун для обучения или же создать самостоятельно. Курс также включает в себя детальное обсуждение тем, таких как техника безопасности, выбор инструментов, диагностика, чистка негатива, и понятия защиты в различных аспектах магии.\n\nПереходите по кнопке ниже👇 и напишите мне ХОЧУ ПРОБНЫЙ УРОК ПО РУНАМ\n_____________\n\nЦена полного доступа: 10.000 рублей", reply_markup=keyboard)

    if call.data == "feedback":
        btn1 = InlineKeyboardButton(text= "Узнать стоимость", url='https://t.me/valeriya_astropsy')
        keyboard = InlineKeyboardMarkup().add(btn1)
    
        bot.send_media_group(call.message.chat.id, [InputMediaPhoto(open('1.png', 'rb'), ), InputMediaPhoto(open('2.png', 'rb')), InputMediaPhoto(open('3.png', 'rb')), InputMediaPhoto(open('4.png', 'rb')), InputMediaPhoto(open('5.png', 'rb')), InputMediaPhoto(open('6.png', 'rb')), InputMediaPhoto(open('7.png', 'rb'))])
        bot.send_message(call.message.chat.id, "На скриншотах отзывы учеников по работе с Таро и о результатах рунической магии☝️\n\nЯ принимаю на консультацию через личные сообщения: @valeriya_astropsy\n\nКакие услуги я предлагаю:\n\n- Диагностика и проработка психологического состояния с помощью Метафорических ассоциативных карт (МАК);\n- Астро-психологический разбор вашего запроса;\n- Ответы на вопросы с помощью карт Таро;\n- Астро-психологический прогноз на год (Годовой соляр);\n- Определение предназначения с помощью натальной карты;\n- Релокация натальной карты;\n- Гипноз;\n- Диагностика негатива;\n- Магическая работа (чистки и гармонизации).", reply_markup=keyboard)






###################### ЗАПУСК БОТА ######################

while True:
    try:
        bot.infinity_polling(allowed_updates = telebot.util.update_types)
    except:
        continue