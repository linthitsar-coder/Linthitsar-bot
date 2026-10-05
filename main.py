import os
import threading

from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================
# Flask Web Server
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )


threading.Thread(
    target=run_web,
    daemon=True
).start()


# =========================
# Telegram Bot
# =========================

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError(
        "BOT_TOKEN မတွေ့ပါ။ Render Environment မှာ BOT_TOKEN ထည့်ပါ။"
    )


bot = telebot.TeleBot(TOKEN)


# =========================
# START MENU
# =========================

@bot.message_handler(commands=["start"])
def main_menu(message):

    markup = InlineKeyboardMarkup(row_width=1)

    btn1 = InlineKeyboardButton(
        "📚 သင်တန်းများကြည့်ရန်",
        callback_data="courses"
    )

    btn2 = InlineKeyboardButton(
        "📞 ဆက်သွယ်ရန်",
        callback_data="contact"
    )

    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        "မင်္ဂလာပါ 👋\n\n"
        "အောက်ပါ Menu မှ ရွေးချယ်ပါ။",
        reply_markup=markup
    )


# =========================
# BUTTON HANDLER
# =========================

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):

    bot.answer_callback_query(call.id)

    if call.data == "courses":

        bot.send_message(
            call.message.chat.id,
            "📚 သင်တန်းအသေးစိတ်\n\n"
            "Facebook / TikTok ကိုယ်တိုင် Boost လုပ်နည်း\n\n"
            "💰 သင်တန်းကြေး - ၁ သိန်းကျပ်\n"
            "♾️ Lifetime Access\n"
            "📱 Telegram Private Channel"
        )

    elif call.data == "contact":

        bot.send_message(
            call.message.chat.id,
            "📞 ဆက်သွယ်ရန်\n\n"
            "Viber / Telegram\n"
            "09-981236668"
        )


# =========================
# RUN BOT
# =========================

print("🤖 Telegram Bot is starting...")

bot.infinity_polling(
    skip_pending=True,
    timeout=30,
    long_polling_timeout=30
)
