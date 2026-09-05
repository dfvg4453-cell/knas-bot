import os
import json
import random
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# ----------------- خادم إبقاء الخدمة نشطة -----------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# ----------------- الإعدادات والملفات -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ خطأ: BOT_TOKEN غير محدد!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 123456789  # ضع ايدي حسابك هنا
INVITE_BONUS = 0.01

USERS_FILE = 'users.json'
NUMBERS_FILE = 'numbers.json'

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {} if 'users' in file_path else []
    return {} if 'users' in file_path else []

def save_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطأ بالحفظ: {e}")

users_data = load_json(USERS_FILE)

# قائمة الفئات والأسعار الافتراضية
CATEGORIES = {
    "cat_2022": {"title": "2022", "price": 1.0, "filter_year": 2022},
    "cat_2023": {"title": "2023", "price": 0.6, "filter_year": 2023},
    "cat_2021": {"title": "2021", "price": 1.2, "filter_year": 2021},
    "cat_2020": {"title": "2020", "price": 1.8, "filter_year": 2020},
    "cat_usa": {"title": "🇺🇸 USA", "price": 0.25, "code": "+1"},
    "cat_india": {"title": "🇮🇳 India", "price": 0.22, "code": "+91"},
    "cat_saudi": {"title": "🇸🇦 Saudi Arabia", "price": 1.0, "code": "+966"},
    "cat_russia": {"title": "🇷🇺 Russia", "price": 1.4, "code": "+7"},
    "cat_turkey": {"title": "🇹🇷 Türkiye", "price": 1.0, "code": "+90"},
    "cat_chile": {"title": "🇨🇱 Chile", "price": 0.3, "code": "+56"},
    "cat_spam": {"title": "❗ Spam mix", "price": 0.12, "code": "mix"}
}

def get_stock_count(cat_key):
    numbers = load_json(NUMBERS_FILE)
    cat_info = CATEGORIES.get(cat_key, {})
    count = 0
    for num in numbers:
        if "code" in cat_info and cat_info["code"] != "mix":
            if num.get("phone", "").startswith(cat_info["code"]):
                count += 1
        elif "filter_year" in cat_info:
            if num.get("year") == cat_info["filter_year"]:
                count += 1
        elif cat_info.get("code") == "mix":
            count += 1
    return count

# ----------------- لوحات المفاتيح والأزرار -----------------

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("☎️ شراء حسابات", callback_data="buy_menu"),
        types.InlineKeyboardButton("📦 session json", callback_data="session_menu"),
        types.InlineKeyboardButton("💳 شحن الرصيد", callback_data="recharge"),
        types.InlineKeyboardButton("👥 تحويل الرصيد", callback_data="transfer"),
        types.InlineKeyboardButton("🎁 تجميع النقاط", callback_data="referral"),
        types.InlineKeyboardButton("💬 الدعم", callback_data="support"),
        types.InlineKeyboardButton("📍 الاحصائيات", callback_data="stats"),
        types.InlineKeyboardButton("⚡ كود خصم", callback_data="promo_code"),
        types.InlineKeyboardButton("⚙️ القوانين", callback_data="rules")
    )
    return markup

def get_buy_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat_key, cat_data in CATEGORIES.items():
        stock = get_stock_count(cat_key)
        btn_text = f"{cat_data['title']} | {cat_data['price']}$ | {stock}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{cat_key}"))
    markup.add(
        types.InlineKeyboardButton("AUTO", callback_data="buy_auto"),
        types.InlineKeyboardButton("🔄 رجوع", callback_data="back_home")
    )
    return markup

# ----------------- معالجة الأوامر والإنلاين -----------------

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    if user_id not in users_data:
        users_data[user_id] = {"balance": 0.2, "invited_by": None}
        save_json(USERS_FILE, users_data)

    if len(args) > 1 and users_data[user_id]["invited_by"] is None:
        referrer_id = str(args[1])
        if referrer_id != user_id and referrer_id in users_data:
            users_data[user_id]["invited_by"] = referrer_id
            users_data[referrer_id]["balance"] += INVITE_BONUS
            save_json(USERS_FILE, users_data)

    balance = users_data[user_id]["balance"]
    name = message.from_user.first_name
    
    text = (
        f"أهلاً بك مجدداً في بوت\n"
        f" ( نوير للأرقام الوهمية ) 📑\n\n"
        f"• ايدي حسابك: `{user_id}`\n"
        f"• رصيدك: **{balance:.1f} $**"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id

    if user_id not in users_data:
        users_data[user_id] = {"balance": 0.0, "invited_by": None}
        save_json(USERS_FILE, users_data)

    if call.data == "buy_menu":
        bot.edit_message_text(
            "اختر الرقم الذي تريده من القائمة:",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=get_buy_menu()
        )

    elif call.data == "back_home":
        balance = users_data[user_id]["balance"]
        text = (
            f"أهلاً بك مجدداً في بوت\n"
            f" ( نوير للأرقام الوهمية ) 📑\n\n"
            f"• ايدي حسابك: `{user_id}`\n"
            f"• رصيدك: **{balance:.1f} $**"
        )
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

    elif call.data.startswith("buy_cat_"):
        cat_key = call.data.replace("buy_", "")
        cat_data = CATEGORIES.get(cat_key)
        
        if not cat_data:
            bot.answer_callback_query(call.id, "الفئة غير متوفرة حالياً")
            return

        price = cat_data["price"]
        current_balance = users_data[user_id]["balance"]

        if current_balance < price:
            bot.answer_callback_query(call.id, f"❌ رصيدك غير كافٍ! سعر القسم هو {price}$ ورصيدك {current_balance:.2f}$", show_alert=True)
            return

        numbers = load_json(NUMBERS_FILE)
        selected_index = -1

        for idx, num in enumerate(numbers):
            if "code" in cat_data and cat_data["code"] != "mix":
                if num.get("phone", "").startswith(cat_data["code"]):
                    selected_index = idx
                    break
            elif "filter_year" in cat_data:
                if num.get("year") == cat_data["filter_year"]:
                    selected_index = idx
                    break
            elif cat_data.get("code") == "mix":
                selected_index = idx
                break

        if selected_index == -1:
            bot.answer_callback_query(call.id, "❌ لا تتوفّر أرقام في هذه الفئة حالياً!", show_alert=True)
            return

        selected_item = numbers.pop(selected_index)
        save_json(NUMBERS_FILE, numbers)

        users_data[user_id]["balance"] -= price
        save_json(USERS_FILE, users_data)

        phone = selected_item['phone']

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📩 طلب كود التحقق", callback_data=f"get_code_{phone}"))

        text = (
            f"✅ **تم شراء الرقم بنجاح!**\n\n"
            f"📱 الرقم: `+{phone}`\n"
            f"💰 الخصم: **{price}$**\n"
            f"💳 الرصيد المتبقي: **{users_data[user_id]['balance']:.2f}$**\n\n"
            f"اضغط على الزر أدناه لجلب الكود عند طلبه."
        )
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support":
        bot.answer_callback_query(call.id, "للتواصل مع الدعم الفني: @K5XYY", show_alert=True)

    elif call.data == "recharge":
        bot.answer_callback_query(call.id, "للشحن عبر آسيا أو ماستر كارد تواصل مع: @K5XYY", show_alert=True)

# ----------------- تشغيل البوت -----------------
if __name__ == "__main__":
    print("🚀 البوت يعمل بالواجهة المحدّثة...")
    while True:
        try:
            bot.polling(non_stop=True, interval=1, timeout=30)
        except Exception as e:
            time.sleep(5)
