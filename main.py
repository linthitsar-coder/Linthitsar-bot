import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '8986301041:AAGN0UntBI7OkJNQoGZERn4xSmoq1U-bdYU' # မိမိ၏ Bot Token ကို ဒီမှာ ထည့်ပါ
telebotbot = .TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def main_menu(message):
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("📚 သင်တန်းများကြည့်ရန်", callback_data="courses")
    btn2 = InlineKeyboardButton("📞 ဆက်သွယ်ရန်", callback_data="contact")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "မင်္ဂလာပါ၊ အောက်ပါ Menu မှ ရွေးချယ်ပါ -", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "courses":
        bot.send_message(call.message.chat.id, "သင်တန်း အသေးစိတ်...")
    elif call.data == "contact":
        bot.send_message(call.message.chat.id, "ဆက်သွယ်ရန်...")

bot.infinity_polling()

