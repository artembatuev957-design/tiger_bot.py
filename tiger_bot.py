import telebot
import requests
import base64
from currency_converter import CurrencyConverter
from telebot import types
import urllib3
import uuid

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. НАСТРОЙКИ (ТВОИ КЛЮЧИ) ---
TOKEN = '8452228553:AAHhIdVrTxs7R2AcmRg1m-0CU0J3YEguoiI'
YANDEX_API_KEY = 'AQVN3XxOIh9d4lm4DIrN4R9-dFx8L4Qc1XeWcgYd'
FOLDER_ID = 'b1g63urksn5r48sftd80'
WEATHER_API = '5c9a7eb45c7040dfef95ed49a576f363'

CLIENT_ID = '019c6cea-f769-765f-9537-b1fb14b87424'
CLIENT_SECRET = 'c7edfff7-97bd-4b0f-892a-941804d5edcf'
auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
GIGA_AUTH_KEY = base64.b64encode(auth_str.encode()).decode()

bot = telebot.TeleBot(TOKEN)
currency = CurrencyConverter()
tiger_status = {}
tiger_wallet = {}


def reset_tiger(chat_id):
    tiger_status[chat_id] = None


# --- 2. МОЗГИ ТИГРА (ИИ И РИСОВАНИЕ) ---

def tiger_think(text):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.3},  # Низкая температура для точности
        "messages": [
            {
                "role": "system",
                "text": "Ты — полезный ассистент в стиле крутого тигра. Давай только четкие, правдивые и полезные ответы. Не болтай лишнего, помогай по факту. Отвечай кратко."
            },
            {"role": "user", "text": text}
        ]
    }
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        return f"🐯: {res['result']['alternatives'][0]['message']['text']}"
    except:
        return "🐯: Мозги заклинило, бро! Попробуй еще раз."


def tiger_artist(prompt):
    url_auth = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers_auth = {'Authorization': f'Basic {GIGA_AUTH_KEY}', 'Content-Type': 'application/x-www-form-urlencoded',
                    'RqUID': str(uuid.uuid4())}
    try:
        res_auth = requests.post(url_auth, headers=headers_auth, data={'scope': 'GIGACHAT_API_PERS'}, verify=False,
                                 timeout=20)
        token = res_auth.json().get('access_token')
        url_draw = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers_draw = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
        payload_draw = {"model": "GigaChat",
                        "messages": [{"role": "user", "content": f"Сгенерируй изображение: {prompt}"}],
                        "function_call": "auto"}
        res_draw = requests.post(url_draw, headers=headers_draw, json=payload_draw, verify=False, timeout=120)
        content = res_draw.json()['choices'][0]['message']['content']
        if "<img src=" in content:
            file_id = content.split('src="')[1].split('"')[0]
            url_file = f"https://gigachat.devices.sberbank.ru/api/v1/files/{file_id}/content"
            return requests.get(url_file, headers={'Authorization': f'Bearer {token}'}, verify=False).content
        return content
    except:
        return "🐯: Краски высохли, не могу рисовать!"


# --- 3. КОМАНДЫ (КНОПКИ ТИГРА) ---

@bot.message_handler(commands=['start', 'help'])
def tiger_help(message):
    reset_tiger(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('🐯 Чат', '🎨 Фото', '🌥 Погода', '💰 Курс', '🛑 Стоп')

    help_text = "🐯 **Тигр на связи!**\nВыбирай режим кнопкой внизу. Помогу чем смогу! 🐾"
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == '🐯 Чат' or m.text == '/ai')
def mode_ai(message):
    tiger_status[message.chat.id] = 'ai'
    bot.reply_to(message, "🐯 Я слушаю. Спрашивай что угодно, отвечу по делу!")


@bot.message_handler(func=lambda m: m.text == '🎨 Фото' or m.text == '/draw')
def mode_draw(message):
    tiger_status[message.chat.id] = 'draw'
    bot.reply_to(message, "🐯 Что нарисовать?")


@bot.message_handler(func=lambda m: m.text == '🛑 Стоп' or m.text == '/stop')
def mode_stop(message):
    reset_tiger(message.chat.id)
    bot.reply_to(message, "🐯 Ушел в спячку. Если что — пиши /help.")


@bot.message_handler(func=lambda m: m.text == '🌥 Погода' or m.text == '/weather')
def mode_weather(message):
    reset_tiger(message.chat.id)
    msg = bot.send_message(message.chat.id, "🐯 В каком городе проверить?")
    bot.register_next_step_handler(msg, get_tiger_weather)


def get_tiger_weather(message):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={WEATHER_API}&units=metric&lang=ru"
        res = requests.get(url).json()
        bot.reply_to(message, f"🐯 В {message.text} сейчас {res['main']['temp']}°C. Береги лапы!")
    except:
        bot.reply_to(message, "🐯 Не нашел такой город!")


@bot.message_handler(func=lambda m: m.text == '💰 Курс' or m.text == '/valute')
def mode_valute(message):
    reset_tiger(message.chat.id)
    msg = bot.send_message(message.chat.id, "🐯 Сколько меняем? (Введи число):")
    bot.register_next_step_handler(msg, tiger_exchange_step)


def tiger_exchange_step(message):
    try:
        amount = float(message.text.strip())
        tiger_wallet[message.chat.id] = amount
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton('RUB ➡ USD', callback_data='RUB_USD'),
            types.InlineKeyboardButton('RUB ➡ EUR', callback_data='RUB_EUR'),
            types.InlineKeyboardButton('USD ➡ RUB', callback_data='USD_RUB'),
            types.InlineKeyboardButton('EUR ➡ RUB', callback_data='EUR_RUB'),
            types.InlineKeyboardButton('EUR ➡ USD', callback_data='EUR_USD'),
            types.InlineKeyboardButton('USD ➡ EUR', callback_data='USD_EUR')
        )
        bot.send_message(message.chat.id, f"🐯 Направление для {amount}:", reply_markup=markup)
    except:
        bot.reply_to(message, "🐯 Пиши только цифры!")


@bot.callback_query_handler(func=lambda call: '_' in call.data)
def tiger_callback(call):
    if call.message.chat.id not in tiger_wallet: return
    amount = tiger_wallet[call.message.chat.id]
    f, t = call.data.split('_')
    res = round(currency.convert(amount, f, t), 2)
    bot.edit_message_text(f"🐯 Итог: {amount} {f} = **{res} {t}**", call.message.chat.id, call.message.message_id,
                          parse_mode='Markdown')


# --- 4. ОБРАБОТКА ТЕКСТА ---

@bot.message_handler(content_types=['text'])
def handle_tiger_text(message):
    if message.text.startswith('/'): return
    status = tiger_status.get(message.chat.id)
    if status == 'ai':
        bot.reply_to(message, tiger_think(message.text))
    elif status == 'draw':
        bot.reply_to(message, "🐯 Сейчас набросаю шедевр...")
        result = tiger_artist(message.text)
        if isinstance(result, bytes):
            bot.send_photo(message.chat.id, result, caption="🐯 Твой арт готов!")
        else:
            bot.reply_to(message, f"🐯 {result}")
    else:
        bot.reply_to(message, "🐯 Выбери режим кнопкой в меню! 😉")


bot.infinity_polling()