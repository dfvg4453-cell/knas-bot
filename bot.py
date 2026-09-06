import json
import os
import random
import asyncio
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient
from telethon.sessions import StringSession

# التوكن الخاص بك
BOT_TOKEN = "8719055808:AAHHYsemZgR5YL8VTQtmzSenSrt2KRqNx9M"
bot = telebot.TeleBot(BOT_TOKEN)

# معلومات تليجرام API (ضرورية لتشغيل Telethon لسحب الكود)
# يقدر أيهم يخليهم ثوابت أو يسجلهم من my.telegram.org
API_ID = 2040  # مثال (استبدله بـ api_id الخاص بك إذا لزم)
API_HASH = "b18441a1ff607e10a989891a5462e627"

ADMIN_ID = 8564075705
CHANNEL_USERNAME = "KNAS1_BOT"

USERS_FILE = "data.json"
NUMBERS_FILE = "numbers.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "banned": []}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_numbers():
    if os.path.exists(NUMBERS_FILE):
        try:
            with open(NUMBERS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []
    return []

def save_numbers(numbers):
    with open(NUMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(numbers, f, ensure_ascii=False, indent=4)

db = load_users()

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
                db["users"][referrer_id]["balance"] = round(db["users"][referrer_id]["balance"] + 0.01, 4)
                try:
                    bot.send_message(int(referrer_id), "🎉 دخل شخص جديد عبر رابط الدعوة الخاص بك! تم إضافة 0.01$ لرصيدك.")
                except Exception:
                    pass
        save_users(db)

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
            f"• الأرقام المتبقية في الملف: `{len(numbers)}`"
        )
        bot.send_message(call.message.chat.id, stats_msg, parse_mode="Markdown")

    elif call.data == "buy_accounts":
        numbers = load_numbers()
        count = len(numbers)
        price = 0.20
        
        markup = InlineKeyboardMarkup(row_width=1)
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
            bot.answer_callback_query(call.id, f"❌ رصيدك غير كافٍ لشراء الرقم (السعر {price}$)!", show_alert=True)
            return

        index = random.randint(0, len(numbers) - 1)
        selected_item = numbers.pop(index)
        save_numbers(numbers)

        user["balance"] = round(user["balance"] - price, 2)
        save_users(db)

        phone = selected_item.get("phone", "غير معروف")
        session_str = selected_item.get("session", "")

        # نخزن الجلسة ورقم الهاتف في البيانات المؤقتة أو نمررها بـ callback_data بشكل آمن
        # (بما أن الـ callback_data محدود الطول، سنقوم بحفظه مؤقتاً في ملف أو تمرير الـ session)
        # لحل مشكلة طول الـ session، سنقوم بحفظ الأرقام المباعة المؤقتة بدبيشنري أو ملف خاص مؤقت
        temp_file = "sold_temp.json"
        sold_data = {}
        if os.path.exists(temp_file):
            try:
                with open(temp_file, "r", encoding="utf-8") as f:
                    sold_data = json.load(f)
            except:
                pass
        
        # توليد مفتاح عشوائي قصير لتخزين الجلسة ورابط الكود
        import uuid
        trans_id = str(uuid.uuid4())[:8]
        sold_data[trans_id] = {"phone": phone, "session": session_str}
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(sold_data, f)

        markup = InlineKeyboardMarkup()
        btn_code = InlineKeyboardButton("طلب كود 📥", callback_data=f"get_code_{trans_id}")
        markup.add(btn_code)

        success_msg = (
            f"✅ **تم شراء الرقم بنجاح!**\n\n"
            f"📱 الرقم: `{phone}`\n\n"
            f"💰 السعر الخصم: **{price}$**\n"
            f"اضغط على زر (طلب كود) أدناه لجلب كود التحقق من تليجرام."
        )
        bot.send_message(call.message.chat.id, success_msg, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("get_code_"):
        trans_id = call.data.replace("get_code_", "")
        temp_file = "sold_temp.json"
        
        if not os.path.exists(temp_file):
            bot.answer_callback_query(call.id, "❌ انتهت صلاحية الطلب أو تم حذفه.", show_alert=True)
            return
            
        with open(temp_file, "r", encoding="utf-8") as f:
            sold_data = json.load(f)
            
        if trans_id not in sold_data:
            bot.answer_callback_query(call.id, "❌ لم يتم العثور على بيانات هذا الرقم.", show_alert=True)
            return
            
        item_info = sold_data[trans_id]
        phone = item_info["phone"]
        session_str = item_info["session"]

        bot.answer_callback_query(call.id, "⏳ جاري الاتصال بالحساب لجلب الكود...", show_alert=False)

        # دالة غير متزامنة لجلب آخر رسالة من تليجرام (777000)
        async def fetch_telegram_code(sess):
            client = TelegramClient(StringSession(sess), API_ID, API_HASH)
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    return "❌ الجلسة غير مصرح بها أو منتهية الصلاحية."
                
                # جلب آخر رسالة من خدمة تليجرام الرسمية (رقم 777000)
                messages = await client.get_messages(777000, limit=1)
                if messages:
                    msg_text = messages[0].text
                    return f"📥 **آخر رسالة تحقق للرقم `+{phone}`:**\n\n{msg_text}"
                else:
                    return "⚠️ لم يتم العثور على رسالة تحقق جديدة وصلت للرقم بعد."
            except Exception as e:
                return f"❌ حدث خطأ أثناء الاتصال بالجلسة: {str(e)}"
            finally:
                await client.disconnect()

        # تشغيل الـ Asyncio لجلب الكود عبر Telethon
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            code_result = loop.run_until_complete(fetch_telegram_code(session_str))
            loop.close()
            
            bot.send_message(call.message.chat.id, code_result, parse_mode="Markdown")
        except Exception as ex:
            bot.send_message(call.message.chat.id, f"❌ فشل جلب الكود تلقائياً: {str(ex)}")

    bot.answer_callback_query(call.id)

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
        bot.reply_to(message, f"💳 تم إضافة {amount}$ للمستخدم `{target_id}` بنجاح!", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "⚠️ طريقة الاستخدام:\n`/add_balance آيدي_المستخدم المبلغ`", parse_mode="Markdown")

bot.infinity_polling()
