import os
import json
import random
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telebot.async_telebot import AsyncTeleBot
from telebot import types

API_ID = 39020255
API_HASH = "5dffb8c0d0560b353333395e7aa8ace69"
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = AsyncTeleBot(BOT_TOKEN)

ADMIN_ID = 123456789  # ضع ايدي الأدمن الخاص بك هنا

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
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
        with open('numbers.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"خطأ في قراءة numbers.json: {e}")
        return []

def save_numbers(numbers_list):
    with open('numbers.json', 'w', encoding='utf-8') as f:
        json.dump(numbers_list, f, ensure_ascii=False, indent=4)

# ----------------- القائمة الرئيسية والبدء -----------------

@bot.message_handler(commands=['start'])
async def start_cmd(message):
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
                await bot.send_message(int(referrer_id), f"🎉 انضم شخص جديد عبر رابطك! تم إضافة `{INVITE_BONUS}$` إلى رصيدك.")
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
    await bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

# ----------------- التعامل مع الأزرار الرئيسية -----------------

@bot.message_handler(func=lambda m: m.text == "✨ تجميع نقاط")
async def referral_cmd(message):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    text = (
        f"✨ **رابط الدعوة الخاص بك:**\n`{ref_link}`\n\n"
        f"قم بنشر الرابط، وكل شخص يقوم بتفعيل البوت عبر رابطك ستحصل على `{INVITE_BONUS}$` في رصيدك!"
    )
    await bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💬 الدعم الفني")
async def support_cmd(message):
    text = (
        "💬 **الدعم الفني | Support**\n\n"
        "✨ يرجى إرسال المشكلة بختصار مع الدلائل ورقم الحساب، وانتظار الرد. نعمل لخدمتكم دائماً.\n\n"
        "Please send a brief message with proof and the account number, then wait for a reply. Always at your service.\n\n"
        "👨‍💻 Support / الدعم: @K5XYY"
    )
    await bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💳 شحن رصيد")
async def recharge_cmd(message):
    text = (
        "أهلاً بك!\n"
        "يمكنك شحن الرصيد عبر النجوم والاسيا والماستر.\n\n"
        "الاسعار: https://t.me/KNAS1_BOT/9\n"
        "للشحن: @K5XYY"
    )
    await bot.send_message(message.chat.id, text, disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.text == "🛒 شراء رقم (0.20$)")
async def buy_number_cmd(message):
    user_id = str(message.from_user.id)
    
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0.0, "invited_by": None}
        save_users(users_data)

    current_balance = users_data[user_id]["balance"]

    # 🛑 فحص حارم للرصيد
    if current_balance < PRICE_PER_NUMBER:
        await bot.send_message(
            message.chat.id, 
            f"❌ **رصيدك غير كافٍ للشراء!**\n\n💰 سعر الرقم: **{PRICE_PER_NUMBER}$**\n💳 رصيدك الحالي: **{current_balance:.2f}$**\n\nيرجى شحن حسابك أولاً بالضغط على زر (💳 شحن رصيد).", 
            parse_mode="Markdown"
        )
        return

    numbers = load_numbers()
    if not numbers:
        await bot.send_message(message.chat.id, "❌ لا توجد أرقام متوفرة حالياً في المخزن!")
        return

    # استخراج الرقم المتاح
    selected_item = numbers.pop(0)
    save_numbers(numbers)

    phone = selected_item['phone']
    country = get_country_name(phone)
    creation_date = generate_random_creation_date()

    # الخصم والحفظ الفوري
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
    await bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ----------------- لوحة تحكم الأدمن -----------------

@bot.message_handler(commands=['admin'])
async def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = (
        "⚙️ **لوحة تحكم الأدمن الرئيسية:**\n\n"
        "🔹 /stats - عرض الإحصائيات الشاملة.\n"
        "🔹 /add_points [ID] [النقاط] - إضافة رصيد لمستخدم.\n"
        "🔹 /remove_points [ID] [النقاط] - خصم رصيد من مستخدم.\n"
        "🔹 /broadcast [الرسالة] - إرسال إذاعة جماعية.\n"
        "🔹 /set_channel [المعرف] - تغيير القناة الإجبارية."
    )
    await bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
async def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = len(users_data)
    total_points = sum(u.get("balance", 0.0) for u in users_data.values())
    text = (
        f"📊 **إحصائيات البوت:**\n\n"
        f"👤 إجمالي المستخدمين: **{total_users}**\n"
        f"💰 إجمالي النقاط المُوزعة: **{total_points:.2f}$**"
    )
    await bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['add_points'])
async def add_points_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, amount = message.text.split()
        target_id = str(target_id)
        amount = float(amount)
        
        if target_id not in users_data:
            users_data[target_id] = {"balance": 0.0, "invited_by": None}

        users_data[target_id]["balance"] += amount
        save_users(users_data)

        await bot.send_message(message.chat.id, f"✅ تم إضافة `{amount}$` لحساب `{target_id}` بنجاح.")
        try:
            await bot.send_message(int(target_id), f"🎉 تم إضافة `{amount}$` إلى رصيدك من قبل الإدارة.")
        except Exception:
            pass
    except Exception:
        await bot.send_message(message.chat.id, "⚠️ استخدام خاطئ. الصيغة الصحيحة:\n`/add_points 123456789 1.0`", parse_mode="Markdown")

@bot.message_handler(commands=['remove_points'])
async def remove_points_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, amount = message.text.split()
        target_id = str(target_id)
        amount = float(amount)

        if target_id in users_data:
            users_data[target_id]["balance"] = max(0.0, users_data[target_id]["balance"] - amount)
            save_users(users_data)
            await bot.send_message(message.chat.id, f"✅ تم خصم `{amount}$` من حساب `{target_id}` بنجاح.")
    except Exception:
        await bot.send_message(message.chat.id, "⚠️ استخدام خاطئ. الصيغة الصحيحة:\n`/remove_points 123456789 1.0`", parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
async def broadcast_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    text_to_send = message.text.replace('/broadcast', '').strip()
    if not text_to_send:
        await bot.send_message(message.chat.id, "⚠️ اكتب الرسالة بعد الأمر مباشرة.")
        return
    
    count = 0
    for uid in users_data.keys():
        try:
            await bot.send_message(int(uid), text_to_send)
            count += 1
        except Exception:
            pass
    await bot.send_message(message.chat.id, f"📢 تم إرسال الإذاعة إلى `{count}` مستخدم.")

if __name__ == "__main__":
    asyncio.run(bot.polling(non_stop=True))
