import json
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# التوكن الخاص بك
BOT_TOKEN = "8929601589:AAGrlw9IES1o2N2MlBjG471dRjaz7w4HZAE"
bot = telebot.TeleBot(BOT_TOKEN)

# آيدي المالك والقناة
ADMIN_ID = 8564075705
CHANNEL_USERNAME = "KNAS1_BOT"  # القناة بدون @

DATA_FILE = "data.json"

# تحميل البيانات من ملف JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "banned": [], "items": []}

# حفظ البيانات إلى ملف JSON
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

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
        save_data(db)
    return db["users"][str_id]

# القائمة الرئيسية
def main_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    btn_buy = InlineKeyboardButton("شراء حسابات 🛒", callback_data="buy_accounts")
    btn_session = InlineKeyboardButton("session json 📄", callback_data="session_json")
    btn_charge = InlineKeyboardButton("شحن الرصيد 💳", callback_data="charge_balance")
    btn_transfer = InlineKeyboardButton("تحويل الرصيد 🔄", callback_data="transfer_balance")
    btn_support = InlineKeyboardButton("الدعم 💬", callback_data="support")
    btn_referral = InlineKeyboardButton("مشاركة وتجميع رصيد 🎁", callback_data="referral")
    
    markup.add(btn_buy)
    markup.add(btn_session)
    markup.add(btn_charge, btn_transfer)
    markup.add(btn_support, btn_referral)

    # زر الإحصائيات للمالك فقط
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

    # التحقق من الحظر
    if user_id in db.get("banned", []):
        bot.send_message(message.chat.id, "❌ أنت محظور من استخدام هذا البوت.")
        return

    # التحقق من الاشتراك الإجباري
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

    # تسجيل المستخدم
    if is_new_user:
        db["users"][str_id] = {"balance": 0.0, "referred_by": None}
        if len(text_args) > 1:
            referrer_id = text_args[1]
            if referrer_id != str_id and referrer_id in db["users"]:
                db["users"][str_id]["referred_by"] = referrer_id
                db["users"][referrer_id]["balance"] = round(db["users"][referrer_id].get("balance", 0.0) + 0.01, 2)
                try:
                    bot.send_message(int(referrer_id), "🎉 دخل شخص جديد عبر رابط الدعوة الخاص بك! تم إضافة 0.01$ لرصيدك.")
                except Exception:
                    pass
        save_data(db)

        # إشعار للمالك بدخول مستخدم جديد
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

# التعامل مع الأزرار
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

    if call.data == "referral":
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        referral_text = (
            f"🎁 **رابط الدعوة الخاص بك:**\n`{referral_link}`\n\n"
            f"شارك الرابط مع أصدقائك، ولكل شخص ينضم عبر رابطك ستحصل على **0.01$** رصيد في حسابك!"
        )
        bot.send_message(call.message.chat.id, referral_text, parse_mode="Markdown")

    elif call.data == "support":
        support_text = (
            "💬 **الدعم الفني | Support**\n\n"
            "✨ يرجى إرسال المشكلة بختصار مع الدلائل ورقم الحساب، وانتظار الرد. نعمل لخدمتكم دائماً.\n\n"
            "Please send a brief message with proof and the account number, then wait for a reply. Always at your service.\n\n"
            "👨‍💻 **Support / الدعم:** @K5XYY"
        )
        bot.send_message(call.message.chat.id, support_text, parse_mode="Markdown")

    elif call.data == "charge_balance":
        charge_text = (
            "أهلاً بك 👋\n"
            "يمكنك شحن الرصيد عبر النجوم والاسيا والماستر\n\n"
            "📊 **الأسعار:** https://t.me/KNAS1_BOT/9\n"
            "💳 **للشحن:** @K5XYY"
        )
        bot.send_message(call.message.chat.id, charge_text, disable_web_page_preview=True)

    elif call.data == "admin_stats" and user_id == ADMIN_ID:
        stats_msg = (
            f"📊 **إحصائيات البوت:**\n\n"
            f"• عدد المستخدمين: `{len(db['users'])}`\n"
            f"• عدد المحظورين: `{len(db.get('banned', []))}`\n"
            f"• عدد السلع والأرقام: `{len(db.get('items', []))}`"
        )
        bot.send_message(call.message.chat.id, stats_msg, parse_mode="Markdown")

    elif call.data == "buy_accounts":
        if not db.get("items"):
            bot.send_message(call.message.chat.id, "لا توجد أرقام أو خدمات متوفرة حالياً.")
            return

        markup = InlineKeyboardMarkup(row_width=1)
        for idx, item in enumerate(db["items"]):
            btn_text = f"{item['country']} | {item['price']}$ | {item['count']} متوفر"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"buy_{idx}"))
        
        bot.send_message(call.message.chat.id, "اختر القسم أو الدولة المطلوبة:", reply_markup=markup)

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
            save_data(db)
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
            save_data(db)
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
        save_data(db)
        bot.reply_to(message, f"💳 تم إضافة {amount}$ للمستخدم `{target_id}` بنجاح!", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "⚠️ طريقة الاستخدام:\n`/add_balance آيدي_المستخدم المبلغ`", parse_mode="Markdown")

@bot.message_handler(commands=['add_item'])
def add_item_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split(maxsplit=3)
        country = args[1]
        price = float(args[2])
        count = int(args[3])

        if "items" not in db:
            db["items"] = []

        db["items"].append({"country": country, "price": price, "count": count})
        save_data(db)
        bot.reply_to(message, f"✅ تم إضافة السلعة بنجاح:\nالدولة: {country}\nالسعر: {price}$\nالعدد: {count}")
    except Exception:
        bot.reply_to(message, "⚠️ طريقة الاستخدام:\n`/add_item الدولة السعر العدد`", parse_mode="Markdown")

bot.infinity_polling()
