import asyncio
import os
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# --- 24/7 Flask Server ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running 24/7 successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# --- Telegram Bot States & Logic ---
WAITING_FOR_UID = 1
WAITING_FOR_AMOUNT = 2
WAITING_FOR_ACTION = 3

BOT_TOKEN = "8545246925:AAGQRQmnpIN5Caf-xb-f6oAHkXMZvJ4HVNo"

# Deposit Amount and corresponding Gift Code Rewards Map
REWARD_MAP = {
    "2,000": "500",
    "3,000": "800",
    "5,000": "1,500",
    "10,000": "3,000",
    "15,000": "5,000",
    "20,000": "7,000",
    "30,000": "10,000",
    "50,000": "20,000"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to the Official Deposit Bonus & Reward Verification Bot!**\n\n"
        "To check your deposit status and receive your exclusive Gift Code reward, please submit your Game UID below.\n\n"
        "👉 **Please enter your Game UID:**"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    return WAITING_FOR_UID


async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_uid = update.message.text
    context.user_data["game_uid"] = user_uid

    # Keyboard layout displaying Deposit Amount and its Bonus Gift Code value
    keyboard = [
        [
            InlineKeyboardButton("💰 2,000 (Bonus: 500)", callback_data="amt_2,000"),
            InlineKeyboardButton("💰 3,000 (Bonus: 800)", callback_data="amt_3,000")
        ],
        [
            InlineKeyboardButton("💰 5,000 (Bonus: 1,500)", callback_data="amt_5,000"),
            InlineKeyboardButton("💰 10,000 (Bonus: 3,000)", callback_data="amt_10,000")
        ],
        [
            InlineKeyboardButton("💰 15,000 (Bonus: 5,000)", callback_data="amt_15,000"),
            InlineKeyboardButton("💰 20,000 (Bonus: 7,000)", callback_data="amt_20,000")
        ],
        [
            InlineKeyboardButton("💰 30,000 (Bonus: 10,000)", callback_data="amt_30,000"),
            InlineKeyboardButton("💰 50,000 (Bonus: 20,000)", callback_data="amt_50,000")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    msg_text = (
        f"✅ **Game UID Received:** `{user_uid}`\n\n"
        "🎁 **First Deposit Reward Offers:**\n"
        "• Deposit **2,000** ➔ Get **500** Bonus Gift Code\n"
        "• Deposit **3,000** ➔ Get **800** Bonus Gift Code\n"
        "• Deposit **5,000** ➔ Get **1,500** Bonus Gift Code\n"
        "• Deposit **10,000** ➔ Get **3,000** Bonus Gift Code\n"
        "• Deposit **15,000** ➔ Get **5,000** Bonus Gift Code\n"
        "• Deposit **20,000** ➔ Get **7,000** Bonus Gift Code\n"
        "• Deposit **30,000** ➔ Get **10,000** Bonus Gift Code\n"
        "• Deposit **50,000** ➔ Get **20,000** Bonus Gift Code\n\n"
        "❓ **How much would you like to make your first deposit?**\n"
        "Please select your planned deposit amount below:"
    )

    await update.message.reply_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")
    return WAITING_FOR_AMOUNT


async def handle_amount_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_amount = query.data.replace("amt_", "")
    reward_amount = REWARD_MAP.get(selected_amount, "Bonus")

    context.user_data["amount"] = selected_amount
    context.user_data["reward"] = reward_amount

    keyboard = [
        [InlineKeyboardButton("✅ Yes, I bound E-Wallet & Deposited", callback_data="action_verify")],
        [InlineKeyboardButton("❌ Check Deposit Status", callback_data="action_verify")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg_text = (
        f"🎯 **Selected First Deposit:** `{selected_amount}`\n"
        f"🎁 **Expected Gift Code Bonus:** `{reward_amount}` Value\n\n"
        "📌 **Verification Notice:**\n"
        "Please bind your E-Wallet number in the game account. After verifying your deposit, your Gift Code will be unlocked.\n\n"
        "Please select your confirmation status below:"
    )

    await query.edit_message_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")
    return WAITING_FOR_ACTION


async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_amount = context.user_data.get("amount", "Selected")
    reward_amount = context.user_data.get("reward", "Bonus")

    # Checking status message (7-8 seconds delay)
    checking_msg = await query.edit_message_text(
        "⏳ **Verifying server records for your deposit and E-Wallet binding...**\n"
        "Please wait 7 to 8 seconds.",
        parse_mode="Markdown"
    )

    await asyncio.sleep(7.5)

    retry_keyboard = [[InlineKeyboardButton("🔄 Re-check Deposit Status", callback_data="retry_check")]]
    reply_markup = InlineKeyboardMarkup(retry_keyboard)

    warning_text = (
        "⚠️ **First Deposit Not Detected!**\n\n"
        f"We checked our system records, but your first deposit of **{selected_amount}** "
        f"(for the **{reward_amount}** Bonus Gift Code) has not been completed yet.\n\n"
        f"👉 **Please complete your first deposit of {selected_amount}** and bind your E-Wallet to unlock your Gift Code."
    )
    
    await checking_msg.edit_text(warning_text, reply_markup=reply_markup, parse_mode="Markdown")
    return WAITING_FOR_ACTION


async def handle_retry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("✅ Yes, I bound E-Wallet & Deposited", callback_data="action_verify")],
        [InlineKeyboardButton("❌ Check Deposit Status", callback_data="action_verify")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Please confirm your status after completing the deposit:",
        reply_markup=reply_markup
    )
    return WAITING_FOR_ACTION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Process cancelled. Type /start to try again.")
    return ConversationHandler.END


def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid)],
            WAITING_FOR_AMOUNT: [CallbackQueryHandler(handle_amount_selection, pattern="^amt_")],
            WAITING_FOR_ACTION: [
                CallbackQueryHandler(handle_action, pattern="^action_verify$"),
                CallbackQueryHandler(handle_retry, pattern="^retry_check$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bonus Reward Bot & Flask server are running 24/7...")
    app.run_polling()


if __name__ == "__main__":
    main()
