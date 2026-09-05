import os
import json
import re
import asyncio
from threading import Thread
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- 1. سيرفر وهمي لإبقاء البوت متصلاً على Railway ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# --- 2. إعدادات البوت والـ API ---
TOKEN = '8929601589:AAGrlw9IES1o2N2MlBjG471dRjaz7w4HZAE'
ADMIN_ID = 8564075705
REQUIRED_CHANNEL = "@KNAS1_BOT"

API_ID = 39020255
API_HASH = '5dffb8c0d0560b353333395e7aa8ace69'

NUMBERS_FILE = 'numbers.json'
USERS_FILE = 'users.json'

bot = telebot.TeleBot(TOKEN)

# --- 3. دوال قراءة وحفظ البيانات ---
def load_data(file):
    if not os.path.exists(file):
        return {} if file == USERS_FILE else []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {} if file == USERS_FILE else []

def save_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return True

# --- 4. دالة جلب كود التحقق باستخدام Telethon ---
async def get_telegram_code(session_string):
    try:
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return "❌ الجلسة منتهية الصلاحية أو غير صالحة."

        # الحصول على آخر رسالة من حساب تليجرام الرسمي (ID: 777000)
        messages = await client.get_messages(777000, limit=3)
        await client.disconnect()

        for msg in messages:
            if msg and msg.text:
                # استخراج الكود المكون من 5 أرقام
                match = re.search(r'\b\d{5}\b', msg.text)
                if match:
                    return match.group(0)
                return msg.text

        return "⚠️ لم يصل أي كود تحقق جديد بعد. يرجى إعادة المحاولة."
    except Exception as e:
        return f"❌ حدث خطأ أثناء جلب الكود: {str(e)}"

# --- 5. أوامر وتفاعلات المستخدمين ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name or "مستخدم"
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون معرف"

    if not check_subscription(message.from_user.id):
        bot.reply_to(message, f"⚠️ يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:\n{REQUIRED_CHANNEL}")
        return

    users = load_data(USERS_FILE)

    if user_id not in users:
        users[user_id] = {"balance": 0.0, "name": first_name}
        save_data(USERS_FILE, users)
        
        notification = (
            f"🔔 **مستخدم جديد دخل البوت!**\n\n"
            f"• الاسم: {first_name}\n"
            f"• المعرف: {username}\n"
            f"• الآيدي: `{user_id}`"
        )
        try:
            bot.send_message(ADMIN_ID, notification, parse_mode='Markdown')
        except Exception:
            pass

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🛒 شراء حسابات', '💳 شحن الرصيد')
    markup.add('🔄 تحويل الرصيد', '💬 الدعم')
    markup.add('🎁 مشاركة وتجميع رصيد', '📊 الإحصائيات')

    balance = users[user_id]["balance"]
    welcome_text = (
        f"أهلاً بك مجدداً في البوت 🛒\n\n"
        f"• ايدي حسابك: `{user_id}`\n"
        f"• رصيدك: {balance} $"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == '🛒 شراء حسابات')
def buy_account(message):
    numbers = load_data(NUMBERS_FILE)
    if not numbers:
        bot.reply_to(message, "لا توجد أرقام متوفرة حالياً.")
        return

    # عرض الرقم الأول المتاح
    item = numbers[0]
    phone = item.get("phone", "رقم غير معروف")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📩 طلب كود التحقق", callback_data=f"get_code_0"))

    bot.reply_to(
        message, 
        f"✅ تم تجهيز الرقم لك:\n\n📱 الرقم: `{phone}`\n\nقم بطلب الكود في تليجرام ثم اضغط على الزر أدناه لجلب الكود:",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('get_code_'))
def handle_get_code(call):
    index = int(call.data.split('_')[2])
    numbers = load_data(NUMBERS_FILE)

    if index >= len(numbers):
        bot.answer_callback_query(call.id, "❌ هذا الرقم لم يعُد متوفراً.")
        return

    bot.answer_callback_query(call.id, "جاري البحث عن الكود...")
    session_string = numbers[index].get("session", "")

    if not session_string:
        bot.send_message(call.message.chat.id, "❌ لا توجد جلسة مفعّلة لهذا الرقم.")
        return

    # تشغيل جلب الكود في حلقة أحداث asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    code_result = loop.run_until_complete(get_telegram_code(session_string))

    bot.send_message(call.message.chat.id, f"🔑 **نتيجة طلب الكود:**\n\n`{code_result}`", parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == '📊 الإحصائيات')
def show_stats(message):
    if message.from_user.id == ADMIN_ID:
        stats_command(message)
    else:
        users = load_data(USERS_FILE)
        user_balance = users.get(str(message.from_user.id), {}).get("balance", 0.0)
        bot.reply_to(message, f"📊 **إحصائيات حسابك:**\n\n• رصيدك الحالي: {user_balance} $", parse_mode='Markdown')

# --- 6. أوامر المالك / الأدمن ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    panel_text = (
        "🛠 **لوحة تحكم الأدمن:**\n\n"
        "• `/admin` - فتح هذه اللوحة.\n"
        "• `/stats` - عرض الإحصائيات.\n"
        "• `/add_session <الرقم> <StringSession>` - إضافة رقم وجلسته.\n"
        "• `/add_points <id> <points>` - إضافة رصيد.\n"
        "• `/remove_points <id> <points>` - خصم رصيد.\n"
        "• `/broadcast <الرسالة>` - إذاعة جماعية.\n"
        "• `/set_channel <@channel>` - تغيير القناة الإجبارية."
    )
    bot.reply_to(message, panel_text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_data(USERS_FILE)
    numbers = load_data(NUMBERS_FILE)
    stats_text = (
        f"📊 **إحصائيات البوت الشاملة:**\n\n"
        f"• عدد المستخدمين: {len(users)}\n"
        f"• إجمالي الرصيد الموزع: {sum(u.get('balance', 0.0) for u in users.values())} $\n"
        f"• عدد الأرقام المتاحة: {len(numbers)}"
    )
    bot.reply_to(message, stats_text, parse_mode='Markdown')

@bot.message_handler(commands=['add_session'])
def add_session_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split(maxsplit=2)
        phone = parts[1]
        session = parts[2]

        numbers = load_data(NUMBERS_FILE)
        numbers.append({"phone": phone, "session": session})
        save_data(NUMBERS_FILE, numbers)

        bot.reply_to(message, f"✅ تم إضافة الرقم والجلسة بنجاح:\n`{phone}`", parse_mode='Markdown')
    except Exception:
        bot.reply_to(message, "⚠️ الاستخدام الصحيح:\n`/add_session +9647700000000 StringSession...`", parse_mode='Markdown')

@bot.message_handler(commands=['add_points'])
def add_points(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, amount = message.text.split()
        users = load_data(USERS_FILE)
        if target_id in users:
            users[target_id]["balance"] += float(amount)
            save_data(USERS_FILE, users)
            bot.reply_to(message, f"✅ تم إضافة {amount} $ لحساب `{target_id}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ المستخدم غير موجود.")
    except Exception:
        bot.reply_to(message, "⚠️ مثال:\n`/add_points 123456789 10`", parse_mode='Markdown')

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        msg_text = message.text.split(maxsplit=1)[1]
        users = load_data(USERS_FILE)
        s, f = 0, 0
        for uid in users:
            try:
                bot.send_message(uid, msg_text)
                s += 1
            except Exception:
                f += 1
        bot.reply_to(message, f"📢 **تمت الإذاعة:** نجح: {s} | فشل: {f}")
    except IndexError:
        bot.reply_to(message, "⚠️ اكتب الرسالة بعد الأمر.")

# --- 7. تشغيل البوت ---
if __name__ == '__main__':
    print("البوت يعمل الآن...")
    bot.infinity_polling(skip_pending=True)
