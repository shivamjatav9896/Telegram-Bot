import telebot
import random
import os
import json
from telebot import types

BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Replace with your bot token
ADMIN_ID = 7134573254         # Replace with your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)

# File paths
approved_file = "approved_users.txt"
referral_file = "referrals.json"

# Load approved users
def load_approved_users():
    if os.path.exists(approved_file):
        with open(approved_file, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_approved_user(user_id):
    with open(approved_file, "a") as f:
        f.write(f"{user_id}\n")

approved_users = load_approved_users()

# Load and save referral data
def load_referrals():
    try:
        if os.path.exists(referral_file):
            with open(referral_file, "r") as f:
                return json.load(f)
    except:
        return {}
    return {}

def save_referrals(data):
    with open(referral_file, "w") as f:
        json.dump(data, f, indent=2)

referrals = load_referrals()

# Prize logic
prizes = [
    ("Rs.20 Cashback", 40),
    ("Rs.50 Cashback", 25),
    ("Free Spin", 15),
    ("Rs.100 UPI Reward", 10),
    ("Better Luck Next Time", 10)
]

def spin_wheel():
    pool = []
    for prize, weight in prizes:
        pool.extend([prize] * weight)
    return random.choice(pool)

# /start with referral & buttons
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    if len(args) > 1:
        referrer_id = args[1]
        if user_id != referrer_id:
            referrals.setdefault(referrer_id, [])
            if user_id not in referrals[referrer_id]:
                referrals[referrer_id].append(user_id)
                save_referrals(referrals)
                if len(referrals[referrer_id]) >= 2 and referrer_id not in approved_users:
                    approved_users.add(referrer_id)
                    save_approved_user(referrer_id)
                    bot.send_message(referrer_id, "🎉 You have referred 2 users! You are now approved to spin.")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Pay Rs.49", callback_data='pay'),
        types.InlineKeyboardButton("My Referrals", callback_data='referrals')
    )
    markup.add(
        types.InlineKeyboardButton("Spin Now", callback_data='spin'),
        types.InlineKeyboardButton("Help", callback_data='help')
    )

    welcome_message = (
        "<b>Welcome to LuckyTurn!</b>\n\n"
        "🎯 Play & Win UPI Cash by spinning the wheel.\n"
        "💰 Pay Rs.49 or Refer 2 users to unlock your chance!"
    )
    bot.send_message(message.chat.id, welcome_message, parse_mode='HTML', reply_markup=markup)

# Handle all inline button callbacks
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    user_id = str(call.from_user.id)

    if call.data == 'pay':
        pay_message = (
            "<b>💳 Pay to Play!</b>\n\n"
            "Send Rs.49 to UPI ID:\n"
            "<code>shivam123@ybl</code>\n\n"
            "📸 Then send payment screenshot to @trickyrewards."
        )
        bot.send_message(call.message.chat.id, pay_message, parse_mode='HTML')

    elif call.data == 'referrals':
        count = len(referrals.get(user_id, []))
        referral_link = f"https://t.me/LuckyTurnUPI_Bot?start={user_id}"
        referral_message = (
            f"<b>👥 My Referrals</b>\n\n"
            f"You have referred <b>{count}</b> users.\n"
            f"Your referral link:\n"
            f"<code>{referral_link}</code>\n\n"
            "Refer 2 users to unlock free spin!"
        )
        bot.send_message(call.message.chat.id, referral_message, parse_mode='HTML')

    elif call.data == 'spin':
        if user_id in approved_users:
            result = spin_wheel()
            spin_message = (
                "🎯 <b>Spinning the wheel...</b>\n\n"
                f"🎁 <b>You won:</b> {result}"
            )
            bot.send_message(call.message.chat.id, spin_message, parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, "❌ You are not approved yet.\nPay Rs.49 or refer 2 users to unlock the spin.")

    elif call.data == 'help':
        help_message = (
            "<b>ℹ️ How to Play</b>\n\n"
            "1️⃣ Pay Rs.49 to: <code>shivam123@ybl</code>\n"
            "2️⃣ Or refer 2 friends using your referral link.\n"
            "3️⃣ Once approved, tap 'Spin Now' to win UPI prizes!"
        )
        bot.send_message(call.message.chat.id, help_message, parse_mode='HTML')

# Admin-only command to approve a user manually
@bot.message_handler(commands=['approve'])
def handle_approve(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    try:
        user_id = message.text.split()[1]
        approved_users.add(user_id)
        save_approved_user(user_id)
        bot.reply_to(message, f"✅ Approved user: {user_id}")
        bot.send_message(user_id, "🎉 You are now approved to spin!\nType /start to begin.")
    except:
        bot.reply_to(message, "❗ Usage: /approve <user_id>")

bot.polling()
