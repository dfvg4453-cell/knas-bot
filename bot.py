import os
import json
import random
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telebot.async_telebot import AsyncTeleBot
from telebot import types

# البيانات الأساسية
API_ID = 39020255
API_HASH = "5dffb8c0d0560b353333395e7aa8ace69"
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = AsyncTeleBot(BOT_TOKEN)

# معرف الأدمن الرئيسي (ضع الايدي الخاص بك هنا)
ADMIN_ID = 123456789  

PRICE_PER_NUMBER = 0.20
INVITE_BONUS = 0.01

# قواعد البيانات المفترضة في الذاكرة
user_balances = {}
invited_users = set()
mandatory_channel = "@KNAS1_BOT"

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
        print(f"خطأ في قراءة الملف: {e}")
        return []

# ----------------- القائمة الرئيسية والبدء -----------------

@bot.message_handler(commands=['start'])
async def start_cmd(message):
    user_id = message.from_user.id
    args = message.text.split()

    # إنشاء حساب للزبون إن لم يكن موجوداً
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    # التعامل مع رابط الدعوة (نظام تجميع النقاط)
    if len(args) > 1 and user_id not in invited_users:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id:
                user_balances[referrer_id] = user_balances.get(referrer_id, 0.0) + INVITE_BONUS
                invited_users.add(user_id)
                await bot.send_message(referrer_id, f"🎉 انضم شخص جديد عبر رابط دعواتك! تم إضافة `{INVITE_BONUS}$` إلى رصيدك.")
        except Exception as e:
            print(f"خطأ في رابط الدعوة: {e}")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 شراء رقم (0.20$)", "💳 شحن رصيد")
    markup.row("✨ تجميع نقاط", "💬 الدعم الفني")

    balance = user_balances[user_id]
    msg = (
        f"أهلاً بك في بوت متجر الأرقام!\n\n"
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
        "✨ يرجى إرسال المشكلة باختصار مع الدلائل ورقم الحساب، وانتظار الرد. نعمل لخدمتكم دائماً.\n\n"
        "Please send a brief message with proof and the account number, then wait for a reply. Always at your service.\n\n"
        "👨‍💻 Support / الدعم: @K5XYY"
    )
    await bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💳 شحن رصيد")
async def recharge_cmd(message):
    text = (
        "أهلاً بك!\n"
        "يمكنك شحن الرصيد عبر النجوم والآسيا والماستر.\n\n"
        "الأسعار: https://t.me/KNAS1_BOT/9\n"
        "للشحن: @K5XYY"
    )
    await bot.send_message(message.chat.id, text, disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.text == "🛒 شراء رقم (0.20$)")
async def buy_number_cmd(message):
    user_id = message.from_user.id
    current_balance = user_balances.get(user_id, 0.0)

    if current_balance < PRICE_PER_NUMBER:
        await bot.send_message(
            message.chat.id, 
            f"❌ رصيدك غير كافٍ للشراء!\nسعر الرقم: **{PRICE_PER_NUMBER}$**\nرصيدك الحالي: **{current_balance:.2f}$**", 
            parse_mode="Markdown"
        )
        return

    numbers = load_numbers()
    if not numbers:
        await bot.send_message(message.chat.id, "❌ لا توجد أرقام متوفرة حالياً في المخزن!")
        return

    selected_item = numbers[0]
    phone = selected_item['phone']
    country = get_country_name(phone)
    creation_date = generate_random_creation_date()

    user_balances[user_id] -= PRICE_PER_NUMBER

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 طلب كود التحقق", callback_data=f"get_code_{phone}"))

    text = (
        f"✅ **تم شراء الرقم بنجاح!**\n\n"
        f"📞 الرقم: `{phone}`\n"
        f"🌍 الدولة: **{country}**\n"
        f"📅 سنة الإنشاء: **{creation_date}**\n"
        f"💰 السعر المخصوم: **{PRICE_PER_NUMBER}$**\n"
        f"💳 رصيدك المتبقي: **{user_balances[user_id]:.2f}$**"
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
    total_users = len(user_balances)
    total_points = sum(user_balances.values())
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
        target_id = int(target_id)
        amount = float(amount)
        user_balances[target_id] = user_balances.get(target_id, 0.0) + amount
        await bot.send_message(message.chat.id, f"✅ تم إضافة `{amount}$` لحساب `{target_id}` بنجاح.")
        await bot.send_message(target_id, f"🎉 تم إضافة `{amount}$` إلى رصيدك من قبل الإدارة.")
    except Exception:
        await bot.send_message(message.chat.id, "⚠️ استخدام خاطئ. الصيغة الصحيحة:\n`/add_points 123456789 1.0`", parse_mode="Markdown")

@bot.message_handler(commands=['remove_points'])
async def remove_points_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, amount = message.text.split()
        target_id = int(target_id)
        amount = float(amount)
        user_balances[target_id] = max(0.0, user_balances.get(target_id, 0.0) - amount)
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
    for uid in user_balances.keys():
        try:
            await bot.send_message(uid, text_to_send)
            count += 1
        except Exception:
            pass
    await bot.send_message(message.chat.id, f"📢 تم إرسال الإذاعة إلى `{count}` مستخدم.")

@bot.message_handler(commands=['set_channel'])
async def set_channel_cmd(message):
    global mandatory_channel
    if message.from_user.id != ADMIN_ID:
        return
    new_channel = message.text.replace('/set_channel', '').strip()
    if new_channel:
        mandatory_channel = new_channel
        await bot.send_message(message.chat.id, f"✅ تم تحديث القناة الإجبارية إلى: {mandatory_channel}")
    else:
        await bot.send_message(message.chat.id, "⚠️ يرجى كتابة معرف القناة الجديد.")

if __name__ == "__main__":
    asyncio.run(bot.polling(non_stop=True))
