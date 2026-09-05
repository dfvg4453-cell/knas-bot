import json
import os
import re
import asyncio
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client

BOT_TOKEN = "8929601589:AAGrlw9IES1o2N2MlBjG471dRjaz7w4HZAE"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 8564075705
CHANNEL_USERNAME = "KNAS1_BOT"
DATA_FILE = "data.json"

# البيانات الخاصة بك
API_ID = 39020255
API_HASH = "5dffb8c0d0560b35333395e7aa8ace69"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "banned": [], "items": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

def check_sub(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return True

def get_user(user_id):
    str_id = str(user_id)
    if str_id not in db["users"]:
        db["users"][str_id] = {"balance": 0.0, "referred_by": None, "active_sessions": {}}
        save_data(db)
    return db["users"][str_id]

def main_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    btn_buy = InlineKeyboardButton("شراء حسابات 🛒", callback_data="buy_accounts")
    btn_charge = InlineKeyboardButton("شحن الرصيد 💳", callback_data="charge_balance")
    btn_transfer = InlineKeyboardButton("تحويل الرصيد 🔄", callback_data="transfer_balance")
    btn_support = InlineKeyboardButton("الدعم 💬", callback_data="support")
    btn_referral = InlineKeyboardButton("مشاركة وتجميع رصيد 🎁", callback_data="referral")
    
    markup.add(btn_buy)
    markup.add(btn_charge, btn_transfer)
    markup.add(btn_support, btn_referral)

    if user_id == ADMIN_ID:
        btn_stats = InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")
        markup.add(btn_stats)

    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if user_id in db.get("banned", []):
        bot.send_message(message.chat.id, "❌ أنت محظور من استخدام هذا البوت.")
        return

    if not check_sub(user_id):
        sub_msg = f"⚠️ **يجب عليك الاشتراك في القناة أولاً:**\n\n🔗 @{CHANNEL_USERNAME}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME}"))
        markup.add(InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription"))
        bot.send_message(message.chat.id, sub_msg, parse_mode="Markdown", reply_markup=markup)
        return

    get_user(user_id)
    user = db["users"][str(user_id)]
    welcome_msg = (
        f"أهلاً بك مجدداً في البوت 🛒\n\n"
        f"• ايدي حسابك: `{user_id}`\n"
        f"• رصيدك: {user['balance']} $"
    )
    bot.send_message(message.chat.id, welcome_msg, parse_mode="Markdown", reply_markup=main_keyboard(user_id))

@bot.message_handler(commands=['add_session'])
def add_session_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split(maxsplit=4)
        if len(args) < 5:
            bot.reply_to(message, "⚠️ **طريقة الاستخدام:**\n`/add_session الدولة السعر الرقم نص_الجلسة`", parse_mode="Markdown")
            return

        country = args[1]
        price = float(args[2])
        phone = args[3]
        session_str = args[4]

        if "items" not in db:
            db["items"] = []

        found = False
        for item in db["items"]:
            if item["country"] == country:
                if "sessions" not in item:
                    item["sessions"] = []
                item["sessions"].append({"phone": phone, "session": session_str})
                found = True
                break

        if not found:
            db["items"].append({
                "country": country,
                "price": price,
                "sessions": [{"phone": phone, "session": session_str}]
            })

        save_data(db)
        bot.reply_to(message, f"✅ تم إضافة الرقم `{phone}` والجلسة بنجاح إلى قسم `{country}`!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء الإضافة:\n`{e}`", parse_mode="Markdown")

@bot.message_handler(commands=['add_balance'])
def add_balance_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()
        target_id = args[1]
        amount = float(args[2])

        if target_id not in db["users"]:
            db["users"][target_id] = {"balance": 0.0, "referred_by": None, "active_sessions": {}}

        db["users"][target_id]["balance"] = round(db["users"][target_id]["balance"] + amount, 2)
        save_data(db)
        bot.reply_to(message, f"💳 تم إضافة {amount}$ للمستخدم `{target_id}` بنجاح!", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "⚠️ طريقة الاستخدام:\n`/add_balance آيدي_المستخدم المبلغ`", parse_mode="Markdown")

async def get_code_from_pyrogram(session_string):
    try:
        async with Client("session_check", api_id=API_ID, api_hash=API_HASH, session_string=session_string) as app:
            async for msg in app.get_chat_history(777000, limit=3):
                if msg.text:
                    code = re.search(r'\b\d{5}\b', msg.text)
                    if code:
                        return code.group(0)
    except Exception:
        return None
    return None

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    str_id = str(user_id)

    if call.data == "buy_accounts":
        if not db.get("items"):
            bot.send_message(call.message.chat.id, "لا توجد أرقام متوفرة حالياً.")
            return

        markup = InlineKeyboardMarkup(row_width=1)
        for idx, item in enumerate(db["items"]):
            sessions_count = len(item.get("sessions", []))
            if sessions_count > 0:
                btn_text = f"{item['country']} | {item['price']}$ | متوفر: {sessions_count}"
                markup.add(InlineKeyboardButton(btn_text, callback_data=f"buy_{idx}"))
        
        if not markup.keyboard:
            bot.send_message(call.message.chat.id, "لا توجد أرقام متوفرة حالياً.")
            return

        bot.send_message(call.message.chat.id, "اختر الدولة أو القسم المطلوب:", reply_markup=markup)

    elif call.data.startswith("buy_"):
        idx = int(call.data.split("_")[1])
        item = db["items"][idx]
        user_balance = db["users"][str_id]["balance"]

        if user_balance < item["price"]:
            bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ للشراء!", show_alert=True)
            return

        if not item.get("sessions"):
            bot.answer_callback_query(call.id, "❌ نفدت الأرقام من هذا القسم!", show_alert=True)
            return

        db["users"][str_id]["balance"] = round(user_balance - item["price"], 2)
        bought_account = item["sessions"].pop(0)
        save_data(db)

        phone_number = bought_account["phone"]
        session_str = bought_account["session"]

        if "active_sessions" not in db["users"][str_id]:
            db["users"][str_id]["active_sessions"] = {}
        db["users"][str_id]["active_sessions"][phone_number] = session_str
        save_data(db)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📩 طلب الكود", callback_data=f"getcode_{phone_number}"))

        success_msg = (
            f"✅ **تم الشراء بنجاح!**\n\n"
            f"• الرقم: `{phone_number}`\n"
            f"• السعر: {item['price']}$\n\n"
            f"افتح التليجرام واطلب الكود للرقم أعلاه، ثم اضغط على زر **(طلب الكود)**."
        )
        bot.send_message(call.message.chat.id, success_msg, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("getcode_"):
        phone_number = call.data.split("_")[1]
        session_str = db["users"][str_id].get("active_sessions", {}).get(phone_number)

        if not session_str:
            bot.answer_callback_query(call.id, "❌ تعذر العثور على الجلسة.", show_alert=True)
            return

        bot.answer_callback_query(call.id, "جاري البحث عن الكود... 🔄")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        code = loop.run_until_complete(get_code_from_pyrogram(session_str))
        loop.close()

        if code:
            bot.send_message(call.message.chat.id, f"🔑 **كود التحقق للرقم (`{phone_number}`):**\n\n`{code}`", parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "⏳ لم يصل الكود بعد، تأكد من طلب الكود من تطبيق التليجرام أولاً ثم حاول مجدداً.")

    bot.answer_callback_query(call.id)

bot.infinity_polling()
