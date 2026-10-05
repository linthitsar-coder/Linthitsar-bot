import os
import threading
import psycopg2

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
    raise ValueError("BOT_TOKEN မတွေ့ပါ။")


# =========================
# Admin ID
# =========================

ADMIN_ID = os.environ.get("ADMIN_ID")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID မတွေ့ပါ။")

ADMIN_ID = int(ADMIN_ID)


# =========================
# Database
# =========================

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL မတွေ့ပါ။")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# =========================
# Initialize Database
# =========================

def init_database():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(255),
            first_name VARCHAR(255),
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_banned BOOLEAN DEFAULT FALSE,
            is_premium BOOLEAN DEFAULT FALSE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_links (
            id SERIAL PRIMARY KEY,
            admin_message_id BIGINT UNIQUE NOT NULL,
            user_id BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("✅ Database initialized")


# =========================
# Save / Update User
# =========================

def save_user(user):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (
            telegram_id,
            username,
            first_name
        )
        VALUES (%s, %s, %s)

        ON CONFLICT (telegram_id)
        DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_activity = CURRENT_TIMESTAMP
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    conn.commit()

    cursor.close()
    conn.close()


# =========================
# Save Message Link
# =========================

def save_message_link(admin_message_id, user_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO message_links (
            admin_message_id,
            user_id
        )
        VALUES (%s, %s)

        ON CONFLICT (admin_message_id)
        DO UPDATE SET
            user_id = EXCLUDED.user_id
    """, (
        admin_message_id,
        user_id
    ))

    conn.commit()

    cursor.close()
    conn.close()


# =========================
# Get User From Admin Reply
# =========================

def get_user_from_message(admin_message_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id
        FROM message_links
        WHERE admin_message_id = %s
    """, (
        admin_message_id,
    ))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return result[0]

    return None


# =========================
# Bot
# =========================

bot = telebot.TeleBot(TOKEN)


# =========================
# Admin Check
# =========================

def is_admin(user_id):

    return user_id == ADMIN_ID


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def main_menu(message):

    save_user(message.from_user)

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
# USER MESSAGE → ADMIN
# =========================

@bot.message_handler(
    func=lambda message: (
        message.chat.type == "private"
        and message.from_user.id != ADMIN_ID
    ),
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "audio",
        "voice",
        "sticker",
        "location",
        "contact"
    ]
)
def receive_user_message(message):

    try:

        # Save user
        save_user(message.from_user)

        username = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else "Username မရှိပါ"
        )

        # User information
        info = bot.send_message(
            ADMIN_ID,
            "📩 User ဆီက Message အသစ်ရောက်လာပါတယ်\n\n"
            f"👤 Name: {message.from_user.first_name}\n"
            f"📱 Username: {username}\n"
            f"🆔 User ID: {message.from_user.id}\n\n"
            "↩️ ဒီ Message ကို Reply လုပ်ပြီး User ဆီ ပြန်ပို့နိုင်ပါတယ်။"
        )

        # Save link
        save_message_link(
            info.message_id,
            message.from_user.id
        )

        # Forward original message
        forwarded = bot.forward_message(
            ADMIN_ID,
            message.chat.id,
            message.message_id
        )

        # Save forwarded message link too
        save_message_link(
            forwarded.message_id,
            message.from_user.id
        )

    except Exception as e:

        print(
            f"❌ User message error: {e}"
        )


# =========================
# ADMIN REPLY → USER
# =========================

@bot.message_handler(
    func=lambda message: (
        message.chat.id == ADMIN_ID
        and message.reply_to_message is not None
    ),
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "audio",
        "voice",
        "sticker"
    ]
)
def admin_reply(message):

    try:

        replied_message_id = (
            message.reply_to_message.message_id
        )

        user_id = get_user_from_message(
            replied_message_id
        )

        if not user_id:

            bot.send_message(
                ADMIN_ID,
                "⚠️ ဒီ Message နဲ့ သက်ဆိုင်တဲ့ User ကို မတွေ့ပါ။\n\n"
                "User Message ရဲ့ Forwarded Message ကို "
                "Reply လုပ်ကြည့်ပါ။"
            )

            return

        # Text message
        if message.content_type == "text":

            bot.send_message(
                user_id,
                "👑 Admin မှ ပြန်လည်ဖြေကြားချက်\n\n"
                + message.text
            )

        else:

            # Media message ကို User ဆီ copy ပို့
            bot.copy_message(
                user_id,
                ADMIN_ID,
                message.message_id
            )

        bot.send_message(
            ADMIN_ID,
            "✅ User ဆီ Message ပြန်ပို့ပြီးပါပြီ။"
        )

    except Exception as e:

        print(
            f"❌ Admin reply error: {e}"
        )

        bot.send_message(
            ADMIN_ID,
            f"❌ Reply Error\n\n{e}"
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

        if not is_admin(call.from_user.id):

            bot.send_message(
                call.message.chat.id,
                "⛔ Admin ခွင့်ပြုချက်မရှိပါ။"
            )

            return

        markup = InlineKeyboardMarkup(row_width=1)

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

        markup.add(
            user_btn,
            stats_btn,
            broadcast_btn
        )

        bot.send_message(
            call.message.chat.id,
            "👑 Admin Panel\n\n"
            "အောက်ပါ Menu မှ ရွေးချယ်ပါ။",
            reply_markup=markup
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
    # USER MANAGEMENT
    # =========================

    if call.data == "admin_users":

        if not is_admin(call.from_user.id):
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users"
        )

        total_users = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        bot.send_message(
            call.message.chat.id,
            "👥 User Management\n\n"
            f"👤 Total Users: {total_users}"
        )

        return


    # =========================
    # STATISTICS
    # =========================

    if call.data == "admin_stats":

        if not is_admin(call.from_user.id):
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users"
        )

        total_users = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE is_premium = TRUE"
        )

        premium_users = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE is_banned = TRUE"
        )

        banned_users = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        bot.send_message(
            call.message.chat.id,
            "📊 Statistics\n\n"
            f"👥 Total Users: {total_users}\n"
            f"👑 Premium Users: {premium_users}\n"
            f"🚫 Banned Users: {banned_users}"
        )

        return


    # =========================
    # BROADCAST
    # =========================

    if call.data == "admin_broadcast":

        if not is_admin(call.from_user.id):
            return

        bot.send_message(
            call.message.chat.id,
            "📢 Broadcast\n\n"
            "ဒီ Feature ကို နောက်အဆင့်မှာ ဆက်တည်ဆောက်ပါမယ်။"
        )

        return


# =========================
# START BOT
# =========================

print("🗄️ Initializing database...")

init_database()

print("🤖 Telegram Bot is starting...")

bot.infinity_polling(
    skip_pending=True,
    timeout=30,
    long_polling_timeout=30
)
