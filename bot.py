import json
import os
import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# التوكن الخاص بك
BOT_TOKEN = "8641214831:AAF-lDVUDbJUTphLvrGy6WksSIvvGzOxGf0"
bot = telebot.TeleBot(BOT_TOKEN)

# آيدي المالك والقناة
ADMIN_ID = 8564075705
CHANNEL_USERNAME = "KNAS1_BOT"  # القناة بدون @

USERS_FILE = "data.json"
NUMBERS_FILE = "numbers.json"  # ملف الأرقام بصيغة JSON

# تحميل بيانات المستخدمين
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "banned": []}

# حفظ بيانات المستخدمين
def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل الأرقام من ملف JSON الخارجي
def load_numbers():
    if os.path.exists(NUMBERS_FILE):
        try:
            with open(NUMBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# حفظ الأرقام
def save_numbers(numbers):
    with open(NUMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(numbers, f, ensure_ascii=False, indent=4)

db = load_users()

# التحقق من اشتراك المستخدم في القناة
def check_sub(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

def get_user(user_id):
    str_id = str(user_id)
    if str_id not in db["users"]:
        db["users"][str_id] = {"balance": 0.0, "referred_by": None}
        save_users(db)
    return db["users"][str_id]

# القائمة الرئيسية بدون نقاط
def main_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    btn_buy = InlineKeyboardButton("شراء حسابات 🛒", callback_data="buy_accounts")
    btn_session = InlineKeyboardButton("session json 📄", callback_data="session_json")
    btn_charge = InlineKeyboardButton("شحن الرصيد 💳", callback_data="charge_balance")
    btn_transfer = InlineKeyboardButton("تحويل الرصيد 🔄", callback_data="transfer_balance")
    btn_support = InlineKeyboardButton("الدعم 💬", callback_data="support")
    btn_points = InlineKeyboardButton("تجميع الرصيد 🎁", callback_data="points")
    
    markup.add(btn_buy)
    markup.add(btn_session)
    markup.add(btn_charge, btn_transfer)
    markup.add(btn_support, btn_points)

    if user_id == ADMIN_ID:
        btn_stats = InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")
        markup.add(btn_stats)

    return markup

# واجهة الاشتراك الإجباري
def sub_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_channel = InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME}")
    btn_check = InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")
    markup.add(btn_channel, btn_check)
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    str_id = str(user_id)

    if user_id in db.get("banned", []):
        bot.send_message(message.chat.id, "❌ أنت محظور من استخدام هذا البوت.")
        return

    if not check_sub(user_id):
        sub_msg = (
            f"⚠️ **عذراً عزيزي، يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:**\n\n"
            f"🔗 @{CHANNEL_USERNAME}\n\n"
            f"اشترك ثم اضغط على زر **(تحقق من الاشتراك)**."
        )
        bot.send_message(message.chat.id, sub_msg, parse_mode="Markdown", reply_markup=sub_keyboard())
        return

    text_args = message.text.split()
    is_new_user = str_id not in db["users"]

    if is_new_user:
        db["users"][str_id] = {"balance": 0.0, "referred_by": None}
        if len(text_args) > 1:
            referrer_id = text_args[1]
            if referrer_id != str_id and referrer_id in db["users"]:
                db["users"][str_id]["referred_by"] = referrer_id
                # إضافة 0.01$ للمُحيل عند دخول شخص جديد من رابطه
                db["users"][referrer_id]["balance"] = round(db["users"][referrer_id]["balance"] + 0.01, 4)
                try:
                    bot.send_message(int(referrer_id), "🎉 دخل شخص جديد عبر رابط الدعوة الخاص بك! تم إضافة 0.01$ لرصيدك.")
                except Exception:
                    pass
        save_users(db)

        try:
            user_name = message.from_user.first_name or "بدون اسم"
            user_username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
            admin_notify = (
                f"👤 **عضو جديد دخل البوت!**\n\n"
                f"• الاسم: {user_name}\n"
                f"• المعرف: {user_username}\n"
                f"• الآيدي: `{user_id}`\n"
                f"• إجمالي المستخدمين: {len(db['users'])}"
            )
            bot.send_message(ADMIN_ID, admin_notify, parse_mode="Markdown")
        except Exception:
            pass

    user = get_user(user_id)
    welcome_msg = (
        f"أهلاً بك مجدداً في البوت 🛒\n\n"
        f"• ايدي حسابك: `{user_id}`\n"
        f"• رصيدك: {user['balance']} $"
    )
    bot.send_message(message.chat.id, welcome_msg, parse_mode="Markdown", reply_markup=main_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    bot_username = bot.get_me().username

    if user_id in db.get("banned", []):
        bot.answer_callback_query(call.id, "❌ أنت محظور من استخدام البوت.", show_alert=True)
        return

    if call.data == "check_subscription":
        if check_sub(user_id):
            bot.answer_callback_query(call.id, "✅ شكرًا لاشتراكك! يمكنك استخدام البوت الآن.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_command(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في القناة بعد!", show_alert=True)
        return

    if not check_sub(user_id):
        bot.answer_callback_query(call.id, "⚠️ يجب عليك الاشتراك بالقناة أولاً!", show_alert=True)
        return

    if call.data == "points":
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        points_text = (
            f"🎁 **تجميع الرصيد عبر الدعوات:**\n\n"
            f"🔗 رابط الدعوة الخاص بك:\n`{referral_link}`\n\n"
            f"شارك الرابط مع أصدقائك، ولكل شخص ينضم عبر رابطك ستحصل على **0.01$** تضاف لرصيدك مباشرةً!"
        )
        bot.send_message(call.message.chat.id, points_text, parse_mode="Markdown")

    elif call.data == "support":
        support_text = (
            "💬 **الدعم الفني | Support**\n\n"
            "✨ يرجى إرسال المشكلة باختصار مع الدلائل ورقم الحساب، وانتظار الرد. نعمل لخدمتكم دائماً.\n\n"
            "👨‍💻 **Support / الدعم:** @K5XYY"
        )
        bot.send_message(call.message.chat.id, support_text, parse_mode="Markdown")

    elif call.data == "charge_balance":
        charge_text = (
            "أهلاً بك 👋\n"
            "يمكنك شحن الرصيد عبر النجوم والآسيا والماستر\n\n"
            "📊 **الأسعار:** https://t.me/KNAS1_BOT/9\n"
            "💳 **للشحن:** @K5XYY"
        )
        bot.send_message(call.message.chat.id, charge_text, disable_web_page_preview=True)

    elif call.data == "transfer_balance":
        bot.send_message(call.message.chat.id, "🔄 قسم تحويل الرصيد قيد الصيانة حالياً.")

    elif call.data == "session_json":
        bot.send_message(call.message.chat.id, "📄 قسم ملفات Session JSON غير متوفر حالياً أو قيد المراجعة.")

    elif call.data == "admin_stats" and user_id == ADMIN_ID:
        numbers = load_numbers()
        stats_msg = (
            f"📊 **إحصائيات البوت:**\n\n"
            f"• عدد المستخدمين: `{len(db['users'])}`\n"
            f"• عدد المحظورين: `{len(db.get('banned', []))}`\n"
            f"• الأرقام المتوفرة في الملف: `{len(numbers)}`"
        )
        bot.send_message(call.message.chat.id, stats_msg, parse_mode="Markdown")

    elif call.data == "buy_accounts":
        numbers = load_numbers()
        count = len(numbers)
        price = 0.20
        
        markup = InlineKeyboardMarkup(row_width=1)
        # زر "دولة عشوائي" بالتنسيق المطلوب (اسم الدولة عشوائي | السعر | العدد)
        btn_text = f"🌐 دولة عشوائي | {price}$ | {count}"
        markup.add(InlineKeyboardButton(btn_text, callback_data="buy_random_number"))
        
        bot.send_message(call.message.chat.id, "اختر القسم المطلوب:", reply_markup=markup)

    elif call.data == "buy_random_number":
        numbers = load_numbers()
        if not numbers:
            bot.answer_callback_query(call.id, "❌ عذراً، لا توجد أرقام متوفرة حالياً!", show_alert=True)
            return

        user = get_user(user_id)
        price = 0.20

        if user["balance"] < price:
            bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ لشراء الرقم (السعر 0.20$)!", show_alert=True)
            return

        # سحب رقم عشوائي من ملف numbers.json
        selected_item = numbers.pop(random.randint(0, len(numbers) - 1))
        save_numbers(numbers)

        # خصم الرصيد
        user["balance"] = round(user["balance"] - price, 2)
        save_users(db)

        phone_val = selected_item.get('phone', selected_item) if isinstance(selected_item, dict) else selected_item
        bot.send_message(call.message.chat.id, f"✅ **تم شراء الرقم بنجاح!**\n\n📱 الرقم: `+{phone_val}`\n💰 السعر الخصم: **{price}$**", parse_mode="Markdown")

    bot.answer_callback_query(call.id)

# ----------------- أوامر المالك -----------------

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        if "banned" not in db:
            db["banned"] = []
        if target_id not in db["banned"]:
            db["banned"].append(target_id)
            save_users(db)
            bot.reply_to(message, f"🚫 تم حظر المستخدم `{target_id}` بنجاح!", parse_mode="Markdown")
        else:
            bot.reply_to(message, "المستخدم محظور بالفعل.")
    except Exception:
        bot.reply_to(message, "⚠️ طريقة الاستخدام:\n`/ban آيدي_الشخص`", parse_mode="Markdown")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        if "banned" in db and target_id in db["banned"]:
            db["banned"].remove(target_id)
            save_users(db)
            bot.reply_to(message, f"✅ تم فك الحظر عن المستخدم `{target_id}` بنجاح!", parse_mode="Markdown")
        else:
            bot.reply_to(message, "المستخدم غير محظور.")
    except Exception:
        bot.reply_to(message, "⚠️ طريقة الاستخدام:\n`/unban آيدي_الشخص`", parse_mode="Markdown")

@bot.message_handler(commands=['add_balance'])
def add_balance_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()
        target_id = args[1]
        amount = float(args[2])

        if target_id not in db["users"]:
            db["users"][target_id] = {"balance": 0.0, "referred_by": None}

        db["users"][target_id]["balance"] = round(db["users"][target_id]["balance"] + amount, 2)
        save_users(db)
        bot.reply_to(message, f"💳 تم إضافة {amount}$ للمستخدم `{target_id}` بنجاح!", parse_Mode="Markdown")
    except Exception:
        bot.reply_to(message, "⚠️ طريقة الاستخدام:\n`/add_balance آيدي_المستخدم المبلغ`", parse_mode="Markdown")

bot.infinity_polling()
