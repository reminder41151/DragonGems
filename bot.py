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

# Naya Bot Token yahan update kar diya gaya hai
BOT_TOKEN = "8545246925:AAGQRQmnpIN5Caf-xb-f6oAHkXMZvJ4HVNo"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to the Official Reward Verification Center!**\n\n"
        "To check your deposit status and claim your exclusive Gift Code, please submit your Game UID below.\n\n"
        "👉 **Please enter your Game UID:**"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    return WAITING_FOR_UID


async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_uid = update.message.text
    context.user_data["game_uid"] = user_uid

    amounts = ["2,000", "3,000", "5,000", "10,000", "15,000", "20,000", "30,000", "50,000"]
    keyboard = []
    
    for i in range(0, len(amounts), 2):
        row = [
            InlineKeyboardButton(f"💰 {amounts[i]}", callback_data=f"amt_{amounts[i]}"),
            InlineKeyboardButton(f"💰 {amounts[i+1]}", callback_data=f"amt_{amounts[i+1]}")
        ]
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    msg_text = (
        f"✅ **Game UID Received:** `{user_uid}`\n\n"
        "❓ **How much would you like to deposit for your first deposit?**\n"
        "Please select your planned deposit amount from the options below:"
    )

    await update.message.reply_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")
    return WAITING_FOR_AMOUNT


async def handle_amount_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_amount = query.data.replace("amt_", "")
    context.user_data["amount"] = selected_amount

    keyboard = [
        [InlineKeyboardButton("✅ Yes, I bound E-Wallet & Deposited", callback_data="action_verify")],
        [InlineKeyboardButton("❌ Check Deposit Status", callback_data="action_verify")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg_text = (
        f"🎯 **Selected First Deposit:** `{selected_amount}`\n\n"
        "📌 **E-Wallet & Deposit Notice:**\n"
        "Please bind your E-Wallet number for the gift code. After checking your deposit, you can get your Gift Code.\n\n"
        "Please confirm your status below:"
    )

    await query.edit_message_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")
    return WAITING_FOR_ACTION


async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_amount = context.user_data.get("amount", "Selected")

    # Checking status message (7-8 seconds delay)
    checking_msg = await query.edit_message_text(
        "⏳ **Checking server records for your deposit and E-Wallet binding...**\n"
        "Please wait 7 to 8 seconds.",
        parse_mode="Markdown"
    )

    await asyncio.sleep(7.5)

    # Har baar yehi message aayega ke deposit nahi kiya
    retry_keyboard = [[InlineKeyboardButton("🔄 Try Re-verifying", callback_data="retry_check")]]
    reply_markup = InlineKeyboardMarkup(retry_keyboard)

    warning_text = (
        "⚠️ **First Deposit Not Detected!**\n\n"
        f"We checked the system records, but your first deposit of **{selected_amount}** has not been completed yet.\n\n"
        "Please complete your first deposit matching the selected amount and bind your E-Wallet to receive your Gift Code."
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
        "Please select your status again after completing the process:",
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
    print("New Bot & Flask server are running 24/7...")
    app.run_polling()


if __name__ == "__main__":
    main()
