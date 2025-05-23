import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler
)
from functools import wraps

from wallet import create_wallet, connect_wallet, get_connected_wallet, disconnect_wallet, sign_transaction
from intent_parser import parse_nft_intent
from transaction_builder import build_and_send_transaction, create_nft
from utils import get_algod_client, generate_unit_name, text_to_number

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_IDS = [int(id_) for id_ in os.getenv("ALLOWED_USER_IDS", "").split(",") if id_]
SESSIONS_FILE = "telegram_sessions.json"

# Conversation states
PASSWORD, MNEMONIC, PASSWORD_FOR_CONNECT, TRANSACTION_PASSWORD = range(4)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
            await update.message.reply_text("❌ Unauthorized access.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE) as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)

def parse_telegram_send_command(args_text):
    import re
    if not args_text:
        return None
    patterns = [
        r'(?P<amount>[\d\.]+|\w+(?:\s+\w+)*)\s*(?:algo|algos|algorand)?\s*to\s+(?P<address>[A-Z2-7]{58})',
        r'send\s+(?P<amount>[\d\.]+|\w+(?:\s+\w+)*)\s*(?:algo|algos|algorand)?\s*to\s+(?P<address>[A-Z2-7]{58})'
    ]
    for pattern in patterns:
        match = re.search(pattern, args_text, re.IGNORECASE)
        if match:
            amount_text = match.group('amount').strip()
            address = match.group('address').strip()
            if amount_text.replace('.', '', 1).isdigit():
                amount = float(amount_text)
            else:
                amount = text_to_number(amount_text)
                if amount is None:
                    continue
            return {
                'action': 'send',
                'amount': amount,
                'token': 'ALGO',
                'recipient': address
            }
    return None

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome {user.first_name} to Algo-Intent Bot!\n"
        "Available commands:\n"
        "/createwallet - Create new wallet\n"
        "/connectwallet - Connect existing wallet\n"
        "/send - Send ALGO\n"
        "/createnft - Create NFT\n"
        "/balance - Check balance\n"
        "/disconnect - Disconnect wallet"
    )

@restricted
async def create_wallet_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    await update.message.reply_text("🔒 Please set a password for your new wallet:")
    sessions[str(user_id)] = {"state": "awaiting_password_for_create"}
    save_sessions(sessions)
    return PASSWORD

@restricted
async def password_received(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    password = update.message.text
    try:
        wallet_data = create_wallet(password)
        sessions[str(user_id)] = {
            "address": wallet_data["address"],
            "encrypted_mnemonic": wallet_data["encrypted_mnemonic"]
        }
        save_sessions(sessions)
        await update.message.reply_text(
            "✅ Wallet created!\n"
            f"Address: `{wallet_data['address']}`\n"
            f"Mnemonic: `{wallet_data['mnemonic']}`\n"
            "⚠️ Save this mnemonic securely!",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    return ConversationHandler.END

@restricted
async def connect_wallet_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    await update.message.reply_text("🔑 Please enter your 25-word mnemonic phrase:")
    sessions[str(user_id)] = {"state": "awaiting_mnemonic"}
    save_sessions(sessions)
    return MNEMONIC

@restricted
async def mnemonic_received(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    mnemonic = update.message.text
    sessions[str(user_id)]["mnemonic"] = mnemonic
    sessions[str(user_id)]["state"] = "awaiting_password_for_connect"
    save_sessions(sessions)
    await update.message.reply_text("🔒 Please set a password to secure this wallet:")
    return PASSWORD_FOR_CONNECT

@restricted
async def password_for_connect_received(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    password = update.message.text
    mnemonic = sessions[str(user_id)]["mnemonic"]
    try:
        wallet_data = connect_wallet(mnemonic, password)
        sessions[str(user_id)] = {
            "address": wallet_data["address"],
            "encrypted_mnemonic": wallet_data["encrypted_mnemonic"]
        }
        save_sessions(sessions)
        await update.message.reply_text(f"✅ Connected to wallet: `{wallet_data['address']}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    return ConversationHandler.END

@restricted
async def send_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    if str(user_id) not in sessions or "address" not in sessions[str(user_id)]:
        await update.message.reply_text("❌ Please connect a wallet first using /connectwallet")
        return
    
    intent_text = ' '.join(context.args)
    parsed = parse_telegram_send_command(intent_text)
    
    if not parsed:
        await update.message.reply_text(
            "❌ Couldn't understand your request.\n"
            "Format: `/send [amount] ALGO to [address]`\n"
            "Example: `/send 0.5 ALGO to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4`",
            parse_mode="Markdown"
        )
        return
    
    try:
        algod_client = get_algod_client()
        result = build_and_send_transaction(
            sender=sessions[str(user_id)]["address"],
            recipient=parsed["recipient"],
            amount=parsed["amount"],
            algod_client=algod_client,
            password=None,
            frontend='telegram'
        )
        
        # If transaction needs approval, show details and ask for password
        if result.get('status') == 'awaiting_approval':
            txn_details = result['txn_details']
            amount_algo = txn_details['amount_microalgos'] / 1_000_000 if txn_details['amount_microalgos'] else 0
            fee_algo = txn_details['fee_microalgos'] / 1_000_000 if txn_details['fee_microalgos'] else 0
            
            # Store transaction details for signing
            context.user_data['pending_txn'] = result['unsigned_txn']
            context.user_data['pending_parsed'] = parsed
            
            await update.message.reply_text(
                f"📝 **Transaction Details:**\n"
                f"From: `{txn_details['from']}`\n"
                f"To: `{txn_details['to']}`\n"
                f"Amount: **{amount_algo:.6f} ALGO**\n"
                f"Fee: {fee_algo:.6f} ALGO\n"
                f"Type: {txn_details['type']}\n\n"
                f"Please enter your wallet password to approve and sign this transaction:",
                parse_mode="Markdown"
            )
            return TRANSACTION_PASSWORD
        else:
            await update.message.reply_text(f"✅ {result['message']}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

@restricted
async def transaction_password_received(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    password = update.message.text
    
    pending_txn = context.user_data.get('pending_txn')
    pending_parsed = context.user_data.get('pending_parsed')
    
    if not pending_txn or not pending_parsed:
        await update.message.reply_text("❌ No pending transaction found.")
        return ConversationHandler.END
    
    try:
        # Sign the transaction with password
        signed_txn = sign_transaction(pending_txn, password=password, frontend='telegram')
        
        # Send the signed transaction
        algod_client = get_algod_client()
        txid = algod_client.send_transaction(signed_txn)
        
        await update.message.reply_text(
            f"✅ **Transaction Successful!**\n"
            f"Amount: {pending_parsed['amount']:.6f} ALGO\n"
            f"To: `{pending_parsed['recipient']}`\n"
            f"Transaction ID: `{txid}`",
            parse_mode="Markdown"
        )
        
        # Clear pending transaction
        context.user_data.pop('pending_txn', None)
        context.user_data.pop('pending_parsed', None)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Transaction failed: {str(e)}")
    
    return ConversationHandler.END

@restricted
async def create_nft_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    if str(user_id) not in sessions or "address" not in sessions[str(user_id)]:
        await update.message.reply_text("❌ Please connect a wallet first using /connectwallet")
        return
    
    intent_text = ' '.join(context.args)
    
    # Simple NFT name parsing
    if not intent_text:
        await update.message.reply_text("❌ Please provide NFT name.\nExample: `/createnft MyAwesome NFT`")
        return
    
    try:
        algod_client = get_algod_client()
        asset_id = create_nft(
            name=intent_text,
            unit_name=generate_unit_name(intent_text),
            total_supply=1,
            description="",
            algod_client=algod_client,
            sender=sessions[str(user_id)]["address"],
            frontend='cli'  # For now, use CLI for NFT (can be enhanced later)
        )
        await update.message.reply_text(f"✅ NFT created! Asset ID: {asset_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

@restricted
async def disconnect_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    if str(user_id) in sessions:
        del sessions[str(user_id)]
        save_sessions(sessions)
    await update.message.reply_text("✅ Wallet disconnected")

@restricted
async def balance_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sessions = load_sessions()
    if str(user_id) not in sessions or "address" not in sessions[str(user_id)]:
        await update.message.reply_text("❌ Please connect a wallet first using /connectwallet")
        return
    try:
        algod_client = get_algod_client()
        account_info = algod_client.account_info(sessions[str(user_id)]["address"])
        balance = account_info.get("amount", 0) / 1_000_000
        await update.message.reply_text(f"💰 Balance: {balance:.6f} ALGO")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Conversation handler for wallet creation
    create_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("createwallet", create_wallet_handler)],
        states={
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_received)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    
    # Conversation handler for wallet connection
    connect_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("connectwallet", connect_wallet_handler)],
        states={
            MNEMONIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, mnemonic_received)],
            PASSWORD_FOR_CONNECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_for_connect_received)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    
    # Conversation handler for transactions
    send_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("send", send_handler)],
        states={
            TRANSACTION_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, transaction_password_received)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(create_conv_handler)
    application.add_handler(connect_conv_handler)
    application.add_handler(send_conv_handler)
    application.add_handler(CommandHandler("createnft", create_nft_handler))
    application.add_handler(CommandHandler("disconnect", disconnect_handler))
    application.add_handler(CommandHandler("balance", balance_handler))
    
    application.run_polling()

if __name__ == "__main__":
    main()
