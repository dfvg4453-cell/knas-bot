import os
import json
import random
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# ----------------- خادم وهمي لإبقاء Railway شغالاً -----------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# تشغيل الخادم الوهمي في مسار جانبي (Thread)
threading.Thread(target=run_health_server, daemon=True).start()

# ----------------- إعدادات التوكن والبوت -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ خطأ: لم يتم تعيين BOT_TOKEN في Variables!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 123456789  # ضع ايدي حسابك هنا

PRICE_PER_NUMBER = 0.20
INVITE_BONUS = 0.01

USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(data):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطأ بالحفظ: {e}")

users_data = load_users()

def get_country_name(phone):
    if phone.startswith("+91"):
        return "الهند 🇮🇳"
    elif phone.startswith("+95"):
        return "ماينمار 🇲🇲"
    elif phone.startswith("+880"):
        return "بنغلاديش 🇧🇩"
    return "دولة غير محددة 🌐"

def generate_random_creation_date():
    years = [2021, 2022, 2023, 2024, 2025]
    return f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.choice(years)}"

def load_numbers():
    try:
        if os.path.exists('numbers.json'):
            with open('numbers.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"خطأ في قراءة numbers.json: {e}")
    return []

def save_numbers(numbers_list):
    try:
        with open('numbers.json', 'w', encoding='utf-8') as f:
            json.dump(numbers_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطأ في حفظ numbers.json: {e}")

# ----------------- التعامل مع الأوامر -----------------

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    if user_id not in users_data:
        users_data[user_id] = {"balance": 0.0, "invited_by": None}
        save_users(users_data)

    if len(args) > 1 and users_data[user_id]["invited_by"] is None:
        referrer_id = str(args[1])
        if referrer_id != user_id and referrer_id in users_data:
            users_data[user_id]["invited_by"] = referrer_id
            users_data[referrer_id]["balance"] += INVITE_BONUS
            save_users(users_data)
            try:
                bot.send_message(int(referrer_id), f"🎉 انضم شخص جديد عبر رابطك! تم إضافة `{INVITE_BONUS}$` إلى رصيدك.")
            except Exception:
                pass

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 شراء رقم (0.20$)", "💳 شحن رصيد")
    markup.row("✨ تجميع نقاط", "💬 الدعم الفني")

    balance = users_data[user_id]["balance"]
    msg = (
        f"أهلاً بك في متجر الأرقام!\n\n"
        f"💳 رصيدك الحالي: **{balance:.2f}$**\n"
        f"💰 سعر الرقم: **{PRICE_PER_NUMBER}$**"
    )
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "✨ تجميع نقاط")
def referral_cmd(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    text = (
        f"✨ **رابط الدعوة الخاص بك:**\n`{ref_link}`\n\n"
        f"قم بنشر الرابط، وكل شخص يقوم بتفعيل البوت عبر رابطك ستحصل على `{INVITE_BONUS}$` في رصيدك!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💬 الدعم الفني")
def support_cmd(message):
    text = (
        "💬 **الدعم الفني | Support**\n\n"
        "✨ يرجى إرسال المشكلة بختصار مع الدلائل ورقم الحساب، وانتظار الرد.\n\n"
        "👨‍💻 Support / الدعم: @K5XYY"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💳 شحن رصيد")
def recharge_cmd(message):
    text = (
        "أهلاً بك!\n"
        "يمكنك شحن الرصيد عبر النجوم والاسيا والماستر.\n\n"
        "الاسعار: https://t.me/KNAS1_BOT/9\n"
        "للشحن: @K5XYY"
    )
    bot.send_message(message.chat.id, text, disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.text == "🛒 شراء رقم (0.20$)")
def buy_number_cmd(message):
    user_id = str(message.from_user.id)
    
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0.0, "invited_by": None}
        save_users(users_data)

    current_balance = users_data[user_id]["balance"]

    if current_balance < PRICE_PER_NUMBER:
        bot.send_message(
            message.chat.id, 
            f"❌ **رصيدك غير كافٍ للشراء!**\n\n💰 سعر الرقم: **{PRICE_PER_NUMBER}$**\n💳 رصيدك الحالي: **{current_balance:.2f}$**\n\nيرجى شحن حسابك أولاً بالضغط على زر (💳 شحن رصيد).", 
            parse_mode="Markdown"
        )
        return

    numbers = load_numbers()
    if not numbers:
        bot.send_message(message.chat.id, "❌ لا توجد أرقام متوفرة حالياً في المخزن!")
        return

    selected_item = numbers.pop(0)
    save_numbers(numbers)

    phone = selected_item['phone']
    country = get_country_name(phone)
    creation_date = generate_random_creation_date()

    users_data[user_id]["balance"] -= PRICE_PER_NUMBER
    save_users(users_data)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 طلب كود التحقق", callback_data=f"get_code_{phone}"))

    text = (
        f"✅ **تم شراء الرقم بنجاح!**\n\n"
        f"📞 الرقم: `{phone}`\n"
        f"🌍 الدولة: **{country}**\n"
        f"📅 سنة الإنشاء: **{creation_date}**\n"
        f"💰 السعر المخصوم: **{PRICE_PER_NUMBER}$**\n"
        f"💳 رصيدك المتبقي: **{users_data[user_id]['balance']:.2f}$**"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ----------------- بداية التشغيل -----------------
if __name__ == "__main__":
    print("🚀 جاري تشغيل البوت...")
    while True:
        try:
            bot.polling(non_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"حدث انقطاع بسيط، إعادة الاتصال خلال 5 ثوانٍ: {e}")
            time.sleep(5)
