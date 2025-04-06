import json
import time
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from config import TOKEN, REWARD_PER_MINE, MINING_COOLDOWN

DB_FILE = 'database.json'

# Загружаем базу
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}

def save_db():
    with open(DB_FILE, 'w') as f:
        json.dump(users, f)

def get_user(user_id):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {
            'balance': 0,
            'last_mine': 0,
            'ref': None,
            'refs': []
        }
    return users[user_id]

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    args = context.args

    user_data = get_user(user.id)

    if args and not user_data['ref']:
        ref_id = args[0]
        if ref_id != str(user.id) and ref_id not in user_data['refs']:
            user_data['ref'] = ref_id
            get_user(ref_id)['refs'].append(str(user.id))
            get_user(ref_id)['balance'] += 5  # Бонус за реферала

    keyboard = [[InlineKeyboardButton("🛠️ Майнить", callback_data='mine')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f"Добро пожаловать! Твой реф. код: `{user.id}`", parse_mode='Markdown', reply_markup=reply_markup)
    save_db()

def mine(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    user_data = get_user(user_id)
    now = time.time()

    if now - user_data['last_mine'] < MINING_COOLDOWN:
        wait = int(MINING_COOLDOWN - (now - user_data['last_mine']))
        query.answer()
        query.edit_message_text(f"⏳ Подожди {wait} сек до следующей попытки.")
        return

    user_data['balance'] += REWARD_PER_MINE
    user_data['last_mine'] = now
    save_db()

    query.answer()
    query.edit_message_text(f"🎉 Вы намайнили {REWARD_PER_MINE} AUC!\n💰 Баланс: {user_data['balance']} AUC")

def balance(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    bal = get_user(user_id)['balance']
    refs = get_user(user_id)['refs']
    update.message.reply_text(f"💰 Баланс: {bal} AUC\n👥 Приглашено: {len(refs)}")

def ref(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    update.message.reply_text(f"🔗 Твоя реферальная ссылка:\nhttps://t.me/{context.bot.username}?start={user_id}")

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("balance", balance))
dp.add_handler(CommandHandler("ref", ref))
dp.add_handler(CallbackQueryHandler(mine, pattern='mine'))

updater.start_polling()
updater.idle()
