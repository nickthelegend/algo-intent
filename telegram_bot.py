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
from ai_intent import AIIntentParser
from wallet import create_wallet, connect_wallet, disconnect_wallet, get_connected_wallet, sign_transaction
from transaction_builder import build_and_send_transaction, create_nft
from utils import get_algod_client, generate_unit_name

# Configuration
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

def parse_nft_command_fallback(text):
    """Fallback NFT parser when AI fails"""
    import re
    
    # Enhanced patterns for NFT creation
    patterns = [
        r"(?i)(create|mint|make)\s+(?:an?\s+)?nft\s+(?:with\s+name\s+|named\s+|called\s+)?(?P<name>[a-zA-Z0-9\s]+)",
        r"(?i)(?:help\s+me\s+)?(create|mint|make)\s+(?:an?\s+)?nft\s+(?:with\s+name\s+|named\s+|called\s+)?(?P<name>[a-zA-Z0-9\s]+)",
        r"(?i)(create|mint|make)\s+(?P<name>[a-zA-Z0-9\s]+)\s+nft"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group('name').strip()
            return {
                'intent': 'create_nft',
                'parameters': {
                    'name': name,
                    'supply': 1,
                    'description': ''
                }
            }
    return None

def parse_send_command_fallback(text):
    """Fallback send parser when AI fails"""
    import re
    
    pattern = r"(?i)(send|transfer|pay)\s+(?P<amount>[\d\.]+|\w+(?:\s+\w+)*)\s+(?:algo|algos)\s+to\s+(?P<address>[A-Z2-7]{58})"
    match = re.search(pattern, text)
    
    if match:
        amount_text = match.group('amount').strip()
        address = match.group('address').strip()
        
        # Convert amount
        try:
            amount = float(amount_text)
        except ValueError:
            from utils import text_to_number
            amount = text_to_number(amount_text)
            if amount is None:
                return None
        
        return {
            'intent': 'send_algo',
            'parameters': {
                'amount': amount,
                'recipient': address
            }
        }
    return None

@restricted
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome {user.first_name} to Algo-Intent Bot!\n"
        "You can use natural language commands like:\n"
        "- 'Create a new wallet'\n"
        "- 'Send 5 ALGO to K54ZT...'\n"
        "- 'Mint an NFT named Dragon'\n"
        "- 'Check my balance'\n"
        "- 'Disconnect my wallet'"
    )

@restricted
async def handle_message(update: Update, context: CallbackContext):
    user_input = update.message.text
    user_id = update.effective_user.id
    
    # Check if we're in a conversation state
    current_state = context.user_data.get('state')
    if current_state:
        return await handle_conversation_state(update, context)
    
    # Parse intent using AI first, then fallback
    parsed = None
    try:
        intent_parser = AIIntentParser()
        parsed = intent_parser.parse(user_input)
        print(f"AI parsed: {parsed}")  # Debug log
    except Exception as e:
        print(f"AI parsing failed: {e}")
    
    # Fallback parsing if AI fails
    if not parsed or parsed.get('intent') == 'unknown':
        # Try NFT fallback
        parsed = parse_nft_command_fallback(user_input)
        if not parsed:
            # Try send fallback
            parsed = parse_send_command_fallback(user_input)
        
        if parsed:
            print(f"Fallback parsed: {parsed}")  # Debug log
    
    if not parsed:
        await update.message.reply_text(
            "❌ I didn't understand that. Try:\n"
            "• 'Create a new wallet'\n"
            "• 'Send 5 ALGO to ADDRESS'\n"
            "• 'Create NFT named Dragon'\n"
            "• 'Check my balance'"
        )
        return
    
    intent = parsed['intent']
    params = parsed.get('parameters', {})
    
    try:
        if intent == 'create_wallet':
            context.user_data['state'] = 'creating_wallet'
            await update.message.reply_text("🔒 Please set a password for your new wallet:")
        elif intent == 'connect_wallet':
            context.user_data['state'] = 'connecting_wallet'
            await update.message.reply_text("🔑 Please enter your 25-word mnemonic phrase:")
        elif intent == 'send_algo':
            await handle_send_transaction(update, context, params)
        elif intent == 'create_nft':
            await handle_nft_creation(update, context, params)
        elif intent == 'disconnect':
            await handle_disconnect(update, context)
        elif intent == 'balance':
            await handle_balance_check(update, context)
        else:
            await update.message.reply_text("❌ Unsupported action")
    except Exception as e:
        print(f"Error in handle_message: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def handle_conversation_state(update: Update, context: CallbackContext):
    """Handle different conversation states"""
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    message_text = update.message.text
    
    if state == 'creating_wallet':
        await handle_wallet_creation_password(update, context, message_text)
    elif state == 'connecting_wallet':
        await handle_mnemonic_input(update, context, message_text)
    elif state == 'connecting_password':
        await handle_connection_password(update, context, message_text)
    elif state == 'transaction_password':
        await handle_transaction_password(update, context, message_text)
    else:
        context.user_data.clear()
        await update.message.reply_text("❌ Invalid state. Please start over.")

async def handle_wallet_creation_password(update: Update, context: CallbackContext, password: str):
    """Handle password for wallet creation"""
    user_id = update.effective_user.id
    
    try:
        wallet_data = create_wallet(password)
        sessions = load_sessions()
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
        context.user_data.clear()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        context.user_data.clear()

async def handle_mnemonic_input(update: Update, context: CallbackContext, mnemonic: str):
    """Handle mnemonic input for wallet connection"""
    context.user_data['mnemonic'] = mnemonic
    context.user_data['state'] = 'connecting_password'
    await update.message.reply_text("🔒 Please set a password to secure this wallet:")

async def handle_connection_password(update: Update, context: CallbackContext, password: str):
    """Handle password for wallet connection"""
    user_id = update.effective_user.id
    mnemonic = context.user_data.get('mnemonic')
    
    try:
        wallet_data = connect_wallet(mnemonic, password)
        sessions = load_sessions()
        sessions[str(user_id)] = {
            "address": wallet_data["address"],
            "encrypted_mnemonic": wallet_data["encrypted_mnemonic"]
        }
        save_sessions(sessions)
        await update.message.reply_text(f"✅ Connected to wallet: `{wallet_data['address']}`", parse_mode="Markdown")
        context.user_data.clear()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        context.user_data.clear()

async def handle_transaction_password(update: Update, context: CallbackContext, password: str):
    """Handle password for transaction signing"""
    try:
        pending_txn = context.user_data.get('pending_txn')
        transaction_type = context.user_data.get('transaction_type', 'send')
        
        if not pending_txn:
            await update.message.reply_text("❌ No pending transaction found.")
            context.user_data.clear()
            return
        
        signed_txn = sign_transaction(pending_txn, password=password, frontend='telegram')
        algod_client = get_algod_client()
        txid = algod_client.send_transaction(signed_txn)
        
        if transaction_type == 'nft':
            from algosdk.transaction import wait_for_confirmation
            confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
            asset_id = confirmed_txn["asset-index"]
            await update.message.reply_text(
                f"✅ **NFT Created Successfully!**\n"
                f"Asset ID: `{asset_id}`\n"
                f"Transaction ID: `{txid}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"✅ **Transaction Successful!**\n"
                f"Transaction ID: `{txid}`",
                parse_mode="Markdown"
            )
        
        context.user_data.clear()
    except Exception as e:
        await update.message.reply_text(f"❌ Transaction failed: {str(e)}")
        context.user_data.clear()

async def handle_send_transaction(update: Update, context: CallbackContext, params: dict):
    """Handle send transaction with Telegram approval"""
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    if str(user_id) not in sessions or "address" not in sessions[str(user_id)]:
        await update.message.reply_text("❌ Please connect a wallet first!")
        return
    
    required_params = ['amount', 'recipient']
    if not all(param in params for param in required_params):
        await update.message.reply_text("❌ Missing transaction details. Example: 'Send 5 ALGO to address'")
        return
    
    try:
        algod_client = get_algod_client()
        result = build_and_send_transaction(
            sender=sessions[str(user_id)]["address"],
            recipient=params['recipient'],
            amount=params['amount'],
            algod_client=algod_client,
            frontend='telegram'
        )
        
        if result.get('status') == 'awaiting_approval':
            context.user_data['pending_txn'] = result['unsigned_txn']
            context.user_data['state'] = 'transaction_password'
            context.user_data['transaction_type'] = 'send'
            
            await update.message.reply_text(
                f"📝 **Transaction Details:**\n"
                f"Amount: **{params['amount']} ALGO**\n"
                f"To: `{params['recipient']}`\n"
                f"Fee: ~0.001 ALGO\n\n"
                f"Please enter your wallet password to confirm:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"✅ {result['message']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Transaction failed: {str(e)}")

async def handle_nft_creation(update: Update, context: CallbackContext, params: dict):
    """Handle NFT creation with Telegram approval"""
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    if str(user_id) not in sessions or "address" not in sessions[str(user_id)]:
        await update.message.reply_text("❌ Please connect a wallet first!")
        return
    
    if 'name' not in params or not params['name']:
        await update.message.reply_text("❌ Missing NFT name. Example: 'Create NFT named Dragon'")
        return
    
    try:
        algod_client = get_algod_client()
        result = create_nft(
            name=params['name'],
            unit_name=generate_unit_name(params['name']),
            total_supply=params.get('supply', 1),
            description=params.get('description', ""),
            algod_client=algod_client,
            sender=sessions[str(user_id)]["address"],
            frontend='telegram'
        )
        
        if isinstance(result, dict) and result.get('status') == 'awaiting_approval':
            context.user_data['pending_txn'] = result['unsigned_txn']
            context.user_data['state'] = 'transaction_password'
            context.user_data['transaction_type'] = 'nft'
            
            await update.message.reply_text(
                f"📝 **NFT Creation Details:**\n"
                f"Name: **{params['name']}**\n"
                f"Supply: {params.get('supply', 1)}\n"
                f"Description: {params.get('description', 'None')}\n"
                f"Fee: ~0.001 ALGO\n\n"
                f"Please enter your wallet password to create this NFT:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"✅ NFT created! Asset ID: {result}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def handle_balance_check(update: Update, context: CallbackContext):
    """Check wallet balance"""
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    if str(user_id) not in sessions or "address" not in sessions[str(user_id)]:
        await update.message.reply_text("❌ Please connect a wallet first!")
        return
    
    try:
        algod_client = get_algod_client()
        account_info = algod_client.account_info(sessions[str(user_id)]["address"])
        balance = account_info.get("amount", 0) / 1_000_000
        await update.message.reply_text(f"💰 **Balance:** {balance:.6f} ALGO", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def handle_disconnect(update: Update, context: CallbackContext):
    """Disconnect wallet"""
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    if str(user_id) in sessions:
        del sessions[str(user_id)]
        save_sessions(sessions)
    
    await update.message.reply_text("✅ Wallet disconnected")

def main():
    """Main function to start the bot"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add /start command handler FIRST
    application.add_handler(CommandHandler("start", start))
    
    # Add main message handler for all text messages (excluding commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot started! Send messages to interact.")
    application.run_polling()

if __name__ == "__main__":
    main()
