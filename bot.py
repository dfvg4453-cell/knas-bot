import os
import json
import random
import time
import telebot
from telebot import types

# ----------------- إعدادات البوت -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ خطأ: لم يتم تعيين BOT_TOKEN في Variables!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 123456789  
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

# الفئات والأسعار
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
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_cat_{cat_key}"))
    
    total_stock = len(load_json(NUMBERS_FILE))
    auto_btn_text = f"عشوائي | 0.20$ | {total_stock}"
    markup.add(
        types.InlineKeyboardButton(auto_btn_text, callback_data="buy_auto"),
        types.InlineKeyboardButton("🔄 رجوع", callback_data="back_home")
    )
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
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
    
    # مسح الأزرار السفلية المزعجة من الشاشة
    try:
        remove_msg = bot.send_message(chat_id, "...", reply_markup=types.ReplyKeyboardRemove())
        bot.delete_message(chat_id, remove_msg.message_id)
    except Exception:
        pass

    text = (
        f"أهلاً بك مجدداً في بوت\n"
        f" ( نوير للأرقام الوهمية ) 📑\n\n"
        f"• ايدي حسابك: `{user_id}`\n"
        f"• رصيدك: **{balance:.1f} $**"
    )
    bot.send_message(chat_id, text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id

    if user_id not in users_data:
        users_data[user_id] = {"balance": 0.2, "invited_by": None}
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

    elif call.data == "buy_auto":
        auto_price = 0.20
        current_balance = users_data[user_id]["balance"]

        if current_balance < auto_price:
            bot.answer_callback_query(call.id, f"❌ رصيدك غير كافٍ! سعر الرقم العشوائي هو {auto_price}$", show_alert=True)
            return

        numbers = load_json(NUMBERS_FILE)
        if not numbers:
            bot.answer_callback_query(call.id, "❌ لا توفر أرقام حالياً!", show_alert=True)
            return

        selected_index = random.randint(0, len(numbers) - 1)
        selected_item = numbers.pop(selected_index)
        save_json(NUMBERS_FILE, numbers)

        users_data[user_id]["balance"] -= auto_price
        save_json(USERS_FILE, users_data)

        phone = selected_item.get('phone', 'غير معروف')
        text = f"✅ **تم شراء رقم عشوائي بنجاح!**\n\n📱 الرقم: `+{phone}`\n💰 السعر: **{auto_price}$**"
        bot.send_message(chat_id, text, parse_mode="Markdown")

    elif call.data.startswith("buy_cat_"):
        cat_key = call.data.replace("buy_cat_", "")
        cat_data = CATEGORIES.get(cat_key)
        
        if not cat_data:
            bot.answer_callback_query(call.id, "الفئة غير متوفرة")
            return

        price = cat_data["price"]
        current_balance = users_data[user_id]["balance"]

        if current_balance < price:
            bot.answer_callback_query(call.id, f"❌ رصيدك غير كافٍ! السعر هو {price}$", show_alert=True)
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
            bot.answer_callback_query(call.id, "❌ لا توفر أرقام في هذه الفئة!", show_alert=True)
            return

        selected_item = numbers.pop(selected_index)
        save_json(NUMBERS_FILE, numbers)

        users_data[user_id]["balance"] -= price
        save_json(USERS_FILE, users_data)

        phone = selected_item['phone']
        text = f"✅ **تم شراء الرقم بنجاح!**\n\n📱 الرقم: `+{phone}`\n💰 الخصم: **{price}$**"
        bot.send_message(chat_id, text, parse_mode="Markdown")

    elif call.data == "support":
        bot.answer_callback_query(call.id, "للتواصل مع الدعم: @K5XYY", show_alert=True)
    elif call.data == "recharge":
        bot.answer_callback_query(call.id, "للتواصل للشحن: @K5XYY", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "القسْم قيد الصيانة حالياً", show_alert=True)

if __name__ == "__main__":
    print("🚀 البوت يعمل...")
    while True:
        try:
            bot.polling(non_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(3)
