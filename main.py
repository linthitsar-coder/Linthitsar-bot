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


# =========================
# Admin ID
# =========================

ADMIN_ID = os.environ.get("ADMIN_ID")

if not ADMIN_ID:
    raise ValueError(
        "ADMIN_ID မတွေ့ပါ။ Render Environment မှာ ADMIN_ID ထည့်ပါ။"
    )

ADMIN_ID = int(ADMIN_ID)


bot = telebot.TeleBot(TOKEN)


# =========================
# Admin Check
# =========================

def is_admin(user_id):
    return user_id == ADMIN_ID


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

    # Admin ဖြစ်ရင် Admin Panel Button ထည့်မယ်
    if is_admin(message.from_user.id):

        admin_btn = InlineKeyboardButton(
            "👑 Admin Panel",
            callback_data="admin_panel"
        )

        markup.add(admin_btn)

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


    # =========================
    # ADMIN PANEL
    # =========================

    if call.data == "admin_panel":

        # Admin ဟုတ်/မဟုတ် ထပ်စစ်မယ်
        if not is_admin(call.from_user.id):

            bot.send_message(
                call.message.chat.id,
                "⛔ Admin ခွင့်ပြုချက်မရှိပါ။"
            )

            return

        admin_markup = InlineKeyboardMarkup(row_width=1)

        user_btn = InlineKeyboardButton(
            "👥 User Management",
            callback_data="admin_users"
        )

        stats_btn = InlineKeyboardButton(
            "📊 Statistics",
            callback_data="admin_stats"
        )

        broadcast_btn = InlineKeyboardButton(
            "📢 Broadcast",
            callback_data="admin_broadcast"
        )

        admin_markup.add(
            user_btn,
            stats_btn,
            broadcast_btn
        )

        bot.send_message(
            call.message.chat.id,
            "👑 Admin Panel\n\n"
            "ကြိုဆိုပါတယ် Admin။\n"
            "အောက်ပါ Menu မှ ရွေးချယ်ပါ။",
            reply_markup=admin_markup
        )

        return


    # =========================
    # COURSES
    # =========================

    if call.data == "courses":

        bot.send_message(
            call.message.chat.id,
            "📚 သင်တန်းအသေးစိတ်\n\n"
            "Facebook / TikTok ကိုယ်တိုင် Boost လုပ်နည်း\n\n"
            "💰 သင်တန်းကြေး - ၁ သိန်းကျပ်\n"
            "♾️ Lifetime Access\n"
            "📱 Telegram Private Channel"
        )

        return


    # =========================
    # CONTACT
    # =========================

    if call.data == "contact":

        bot.send_message(
            call.message.chat.id,
            "📞 ဆက်သွယ်ရန်\n\n"
            "Viber / Telegram\n"
            "09-981236668"
        )

        return


    # =========================
    # FUTURE ADMIN FEATURES
    # =========================

    if call.data == "admin_users":

        if not is_admin(call.from_user.id):
            return

        bot.send_message(
            call.message.chat.id,
            "👥 User Management\n\n"
            "ဒီ Feature ကို Database ထည့်ပြီးနောက် တည်ဆောက်ပါမယ်။"
        )

        return


    if call.data == "admin_stats":

        if not is_admin(call.from_user.id):
            return

        bot.send_message(
            call.message.chat.id,
            "📊 Statistics\n\n"
            "ဒီ Feature ကို Database ထည့်ပြီးနောက် တည်ဆောက်ပါမယ်။"
        )

        return


    if call.data == "admin_broadcast":

        if not is_admin(call.from_user.id):
            return

        bot.send_message(
            call.message.chat.id,
            "📢 Broadcast\n\n"
            "ဒီ Feature ကို User Database တည်ဆောက်ပြီးနောက် ထည့်ပါမယ်။"
        )

        return


# =========================
# RUN BOT
# =========================

print("🤖 Telegram Bot is starting...")

bot.infinity_polling(
    skip_pending=True,
    timeout=30,
    long_polling_timeout=30
)
