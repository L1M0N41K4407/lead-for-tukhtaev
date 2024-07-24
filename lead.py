from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import KeyboardButton, ReplyKeyboardMarkup
import os
import requests
import asyncio

app = Flask(__name__)

# Ваши реальные токены
TOKEN = "7416384453:AAH734DPoJvHh-setqOpGFNwCrRptf_S6p8"
GOOGLE_MAPS_API_KEY = "AIzaSyAZ2ngwWSAJWRbncBZbQqY5_NNOqhnph0E"

bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()
response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo")
print(response.json())
ngrok_url = "https://482c-82-215-98-233.ngrok-free.app"  # Убедитесь, что это актуальный URL

# Функция для получения страны по координатам
def get_country_from_coordinates(latitude: float, longitude: float) -> str:
    url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK' and len(data['results']) > 0:
            for component in data['results'][0]['address_components']:
                if 'country' in component['types']:
                    return component['long_name']
    return 'Mamlakat topilmadi'

# Функция для получения ID получателя лидов
def get_lead_receiver_id():
    # Замените это на вашу логику получения ID чата
    return 'YOUR_LEAD_RECEIVER_CHAT_ID'

# Обработка команды /start
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    keyboard = [[KeyboardButton("Kontaktni ulash", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_html(
        rf'Salom, {user.mention_html()}! Iltimos, kontaktlaringizni ulashing.',
        reply_markup=reply_markup
    )

# Обработка контактов
async def handle_contact(update: Update, context: CallbackContext) -> None:
    contact = update.message.contact
    user = update.effective_user
    username = f'@{user.username}' if user.username else 'Yo\'q'
    context.user_data['contact'] = {
        'username': username,
        'phone_number': contact.phone_number
    }
    keyboard = [[KeyboardButton("Geolokatsiyani yuborish", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        f'Sizning kontaktingiz uchun rahmat, {username}!\nEndi geolokatsiyangizni yuboring.',
        reply_markup=reply_markup
    )

# Обработка геолокации
async def handle_location(update: Update, context: CallbackContext) -> None:
    location = update.message.location
    user = update.effective_user
    latitude = location.latitude
    longitude = location.longitude
    country = get_country_from_coordinates(latitude, longitude)
    contact_data = context.user_data.get('contact')
    if contact_data:
        username = contact_data['username']
        phone_number = contact_data['phone_number']
        lead_message = (f'Yangi lider:\n'
                        f'Foydalanuvchi nomi: {username}\n'
                        f'Telefon raqami: {phone_number}\n'
                        f'Mamlakat: {country}\n'
                        f'Geolokatsiya: Kenglik {latitude}, Uzunlik {longitude}')
        lead_receiver_id = get_lead_receiver_id()
        if lead_receiver_id:
            await context.bot.send_message(chat_id=lead_receiver_id, text=lead_message)
            await update.message.reply_text('Rahmat! Barcha ma\'lumotlaringiz yuborildi.')
        else:
            await update.message.reply_text('Xato: Qabul qiluvchi ID topilmadi.')
        context.user_data.pop('contact', None)
    else:
        await update.message.reply_text('Xato: Kontakt ma\'lumotlari topilmadi.')

# Обработка текстовых сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    user = update.effective_user
    if len(text) > 0:
        await update.message.reply_text(f'Siz yuborgan xabar: {text}')

async def set_webhook():
    ngrok_url = "https://482c-82-215-98-233.ngrok-free.app"  # Замените на ваш новый URL ngrok
    webhook_url = f"{ngrok_url}/webhook"
    await bot.set_webhook(url=webhook_url)

# Настройка бота
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
application.add_handler(MessageHandler(filters.LOCATION, handle_location))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Настройка вебхука
@app.route('/webhook', methods=['POST'])
def webhook():
    print("Webhook received a request")  # Для отладки
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return 'OK', 200



def run_bot():
    # Установка вебхука
    async def set_webhook():
        ngrok_url = "https://482c-82-215-98-233.ngrok-free.app"  # Замените на ваш URL ngrok
        webhook_url = f"{ngrok_url}/webhook"
        await bot.set_webhook(url=webhook_url)

    asyncio.run(set_webhook())

if __name__ == '__main__':
    run_bot()  # Установка вебхука перед запуском Flask
    app.run(host='0.0.0.0', port=4040, debug=True)
