import os
import json
import logging
import re
import hashlib
import time
from datetime import datetime, timedelta
from telegram import Update, MessageEntity
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler
)
from telegram.constants import ParseMode
from functools import wraps
from ai_intent import AIIntentParser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup
from wallet import create_wallet, connect_wallet, sign_transaction
from transaction_builder import build_and_send_transaction, build_and_send_multi_transaction, create_nft, send_nft, send_nft_multi, get_asset_id_from_txid, opt_in_to_asset, opt_out_of_asset
from utils import get_algod_client, generate_unit_name
import tempfile
from ipfs_utils import upload_to_ipfs



# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SESSIONS_FILE = "telegram_sessions.json"
SECURITY_LOG_FILE = "security_events.log"

# Conversation states
PASSWORD, MNEMONIC, PASSWORD_FOR_CONNECT, TRANSACTION_PASSWORD, IMAGE_HANDLING = range(5)

# Security Configuration
MAX_MESSAGE_LENGTH = 1000
MAX_PASSWORD_ATTEMPTS = 3
SESSION_TIMEOUT_HOURS = 24
MAX_TRANSACTIONS_PER_HOUR = 10
WALLET_CONNECTION = "WALLET_CONNECTION"
CREATING_WALLET = "CREATING_WALLET"

# Set up comprehensive logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security logger
security_logger = logging.getLogger("security")
security_handler = logging.FileHandler(SECURITY_LOG_FILE)
security_handler.setFormatter(logging.Formatter("%(asctime)s - SECURITY - %(message)s"))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

async def delete_message_safely(update: Update, context: CallbackContext):
    """Safely delete a message without raising exceptions"""
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except Exception as e:
        logger.warning(f"Could not delete message: {e}")

def log_security_event(user_id, event_type, details=""):
    """Log security-related events"""
    security_logger.info(f"User {user_id} - {event_type} - {details}")

def sanitize_input(text):
    """Sanitize user input to prevent injection attacks"""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    sanitized = sanitized[:MAX_MESSAGE_LENGTH]
    
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script.*?</script>',
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'eval\(',
        r'exec\(',
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()

def validate_algorand_address(address):
    """Validate Algorand address format with additional security checks"""
    if not address or not isinstance(address, str):
        return False
    
    # Basic format validation
    if len(address) != 58:
        return False
    
    # Check for valid base32 characters
    if not re.match(r'^[A-Z2-7]{58}$', address):
        return False
    
    return True

def check_user_rate_limit(user_id, action_type="general"):
    """Check if user is within rate limits"""
    sessions = load_sessions()
    user_key = str(user_id)
    current_time = datetime.now()
    
    if user_key not in sessions:
        return True
    
    user_session = sessions[user_key]
    
    # Check transaction rate limit
    if action_type == "transaction":
        recent_transactions = user_session.get('recent_transactions', [])
        # Remove transactions older than 1 hour
        recent_transactions = [
            tx_time for tx_time in recent_transactions 
            if datetime.fromisoformat(tx_time) > current_time - timedelta(hours=1)
        ]
        
        if len(recent_transactions) >= MAX_TRANSACTIONS_PER_HOUR:
            log_security_event(user_id, "RATE_LIMIT_EXCEEDED", f"Transaction limit: {len(recent_transactions)}")
            return False
        
        # Add current transaction
        recent_transactions.append(current_time.isoformat())
        user_session['recent_transactions'] = recent_transactions
        sessions[user_key] = user_session
        save_sessions(sessions)
    
    return True

def validate_session(user_id):
    """Validate user session and check for expiry"""
    sessions = load_sessions()
    user_key = str(user_id)
    
    if user_key not in sessions:
        return False
    
    user_session = sessions[user_key]
    
    # Check session expiry
    if 'last_activity' in user_session:
        last_activity = datetime.fromisoformat(user_session['last_activity'])
        if datetime.now() - last_activity > timedelta(hours=SESSION_TIMEOUT_HOURS):
            log_security_event(user_id, "SESSION_EXPIRED")
            del sessions[user_key]
            save_sessions(sessions)
            return False
    
    # Update last activity
    user_session['last_activity'] = datetime.now().isoformat()
    sessions[user_key] = user_session
    save_sessions(sessions)
    
    return True

def load_sessions():
    """Load user sessions with error handling"""
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load sessions: {e}")
        # Backup corrupted file
        if os.path.exists(SESSIONS_FILE):
            backup_name = f"{SESSIONS_FILE}.backup.{int(time.time())}"
            os.rename(SESSIONS_FILE, backup_name)
            logger.info(f"Corrupted sessions file backed up as {backup_name}")
    
    return {}

def save_sessions(sessions):
    """Save user sessions securely"""
    try:
        # Write to temporary file first
        temp_file = f"{SESSIONS_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(sessions, f)
        
        # Atomically replace the original file
        os.replace(temp_file, SESSIONS_FILE)
    except IOError as e:
        logger.error(f"Failed to save sessions: {e}")

def parse_nft_command_fallback(text):
    """Improved fallback NFT parser to handle more natural language cases."""
    text = sanitize_input(text)
    if not text:
        return None

    # Pattern: "create 10 nfts name cool style"
    pattern1 = r"(?i)create\s+(\d+)\s+nfts?\s+name\s+([a-zA-Z0-9\s]{1,50})"
    match1 = re.search(pattern1, text)
    if match1:
        supply = int(match1.group(1))
        name = match1.group(2).strip()
        return {
            'intent': 'create_nft',
            'parameters': {
                'name': name,
                'supply': supply
            }
        }

    # Pattern: "create nft name cool style, 10 only"
    pattern2 = r"(?i)create\s+nft\s+name\s+([a-zA-Z0-9\s]{1,50})[, ]+(\d+)\s*(?:only)?"
    match2 = re.search(pattern2, text)
    if match2:
        name = match2.group(1).strip()
        supply = int(match2.group(2))
        return {
            'intent': 'create_nft',
            'parameters': {
                'name': name,
                'supply': supply
            }
        }

    # Existing patterns for "create nft named X with supply Y"
    pattern3 = r"(?i)create\s+nft\s+(?:named|called)?\s*([a-zA-Z0-9\s]{1,50})(?:\s+with\s+supply\s+(\d+))?"
    match3 = re.search(pattern3, text)
    if match3:
        name = match3.group(1).strip()
        supply = int(match3.group(2)) if match3.group(2) else 1
        return {
            'intent': 'create_nft',
            'parameters': {
                'name': name,
                'supply': supply
            }
        }

    return None


def parse_send_command_fallback(text):
    """Secure fallback send parser"""
    text = sanitize_input(text)
    if not text:
        return None
    
    pattern = r"(?i)(send|transfer|pay)\s+(?P<amount>[\d\.]{1,20}|\w+(?:\s+\w+)*)\s+(?:algo|algos)\s+to\s+(?P<address>[A-Z2-7]{58})"
    match = re.search(pattern, text)
    
    if match:
        amount_text = sanitize_input(match.group('amount'))
        address = sanitize_input(match.group('address'))
        
        # Validate address
        if not validate_algorand_address(address):
            return None
        
        # Convert and validate amount
        try:
            amount = float(amount_text)
            if amount <= 0 or amount > 1000000:  # Reasonable limits
                return None
        except ValueError:
            from utils import text_to_number
            amount = text_to_number(amount_text)
            if amount is None or amount <= 0 or amount > 1000000:
                return None
        
        return {
            'intent': 'send_algo',
            'parameters': {
                'amount': amount,
                'recipient': address
            }
        }
    return None

def parse_opt_command_fallback(text):
    """Enhanced fallback parser for opt-in/opt-out commands"""
    text = sanitize_input(text)
    if not text:
        return None
    
    # Patterns for opt-in
    opt_in_patterns = [
        r"(?i)opt\s*in\s+(?:to\s+|for\s+|)(?:nft\s+|asset\s+|asset\s+id\s+|the\s+asset\s+|)(\d+)",
        r"(?i)opt\s*in\s+(\d+)",
    ]
    
    # Patterns for opt-out  
    opt_out_patterns = [
        r"(?i)opt\s*out\s+(?:of\s+|from\s+|for\s+|)(?:nft\s+|asset\s+|asset\s+id\s+|the\s+asset\s+|)(\d+)",
        r"(?i)opt\s*out\s+(\d+)",
    ]
    
    # Check opt-in patterns
    for pattern in opt_in_patterns:
        match = re.search(pattern, text)
        if match:
            return {
                'intent': 'opt_in',
                'parameters': {
                    'asset_id': int(match.group(1))
                }
            }
    
    # Check opt-out patterns
    for pattern in opt_out_patterns:
        match = re.search(pattern, text)
        if match:
            return {
                'intent': 'opt_out',
                'parameters': {
                    'asset_id': int(match.group(1))
                }
            }
    
    return None

async def start(update: Update, context: CallbackContext):
    """Welcome message for all users"""
    user = update.effective_user
    user_id = user.id
    log_security_event(user_id, "BOT_STARTED", f"Username: {user.username}, Name: {user.first_name}")
    
    keyboard = [
        [
            InlineKeyboardButton(
                "Create Wallet",
                switch_inline_query_current_chat="Create a wallet"
            )
        ],
        [
            InlineKeyboardButton(
                "Connect Wallet",
                switch_inline_query_current_chat="Connect wallet"
            )
        ],
        [
            InlineKeyboardButton(
                "Send ALGO",
                switch_inline_query_current_chat="Send [amount] ALGO to [address]"
            )
        ],
        [
            InlineKeyboardButton(
                "Create NFT",
                switch_inline_query_current_chat="Create NFT named [name] with description [desc]"
            )
        ],
        [
            InlineKeyboardButton(
                "Send NFT",
                switch_inline_query_current_chat="Send NFT [assetID] to [address]"
            )
        ],
        [
            InlineKeyboardButton(
                "Opt-in to Asset",
                switch_inline_query_current_chat="Opt-in to NFT [asset_id]"
            )
        ],
        [
            InlineKeyboardButton(
                "Opt-out of Asset",
                switch_inline_query_current_chat="Opt out of asset [asset_id]"
            )
        ],
        [
            InlineKeyboardButton(
                "Check Balance",
                switch_inline_query_current_chat="Check balance"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Welcome {user.first_name} to Algo-Intent Bot!\n"
        "Choose an action below or type your request in plain English.\n"
        "You can cancel any command at any time with /cancel\n"
        "⚠️ Security Notice: Never share your wallet passwords or mnemonic phrases with anyone!\n"
        "🔐 All sensitive information is automatically deleted from chat for your security.",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: CallbackContext):
    """Main message handler with comprehensive security"""
    user = update.effective_user
    user_id = user.id
    user_input = sanitize_input(update.message.text)
    
    if not user_input:
        await delete_message_safely(update, context)
        await update.message.reply_text("❌ Invalid input received.")
        return
    
    # Rate limiting check
    if not check_user_rate_limit(user_id):
        await update.message.reply_text("⏱️ You're sending requests too quickly. Please wait a moment and try again.")
        return
    
    # Check conversation state
    current_state = context.user_data.get('state')
    if current_state:
        return await handle_conversation_state(update, context)
    
    # Log user interaction (without sensitive data)
    logger.info(f"User {user_id} ({user.username}): {user_input[:50]}...")
    
    # Parse intent
    parsed = None
    try:
        intent_parser = AIIntentParser()
        parsed = intent_parser.parse(user_input)
    except Exception as e:
        logger.error(f"AI parsing failed for user {user_id}: {e}")
    
    # Fallback parsing
    if not parsed or parsed.get('intent') == 'unknown':
        parsed = parse_nft_command_fallback(user_input)
        if not parsed:
            parsed = parse_send_command_fallback(user_input)
    
    if not parsed:
        await update.message.reply_text(
            "❌ I didn't understand that command.\n\n"
            "Try:\n"
            "• 'Create a new wallet'\n"
            "• 'Send 5 ALGO to [ADDRESS]'\n"
            "• 'Create NFT named Dragon'\n"
            "• 'Check my balance'"
        )
        return
    
    intent = parsed['intent']
    params = parsed.get('parameters', {})
    
    try:
        if intent == 'create_wallet':
            log_security_event(user_id, "WALLET_CREATION_INITIATED")
            context.user_data['state'] = 'creating_wallet'
            await update.message.reply_text(
                "🔒 Creating a new wallet...\n"
                "Please set a secure password (minimum 8 characters):\n\n"
                "🔐 Your password will be automatically deleted for security."
            )
        elif intent == 'connect_wallet':
            log_security_event(user_id, "WALLET_CONNECTION_INITIATED")
            context.user_data['state'] = 'connecting_wallet'
            await update.message.reply_text(
                "🔑 Connecting to existing wallet...\n"
                "Please enter your 25-word mnemonic phrase:\n\n"
                "🔐 Your mnemonic will be automatically deleted for security."
            )
        elif intent == 'send_algo':
            await handle_send_transaction(update, context, params)
        elif intent == 'send_algo_multi':
            await handle_multi_send_transaction(update, context, params)
        elif intent == 'create_nft':
            await handle_nft_creation(update, context, params)
        elif intent == 'send_nft':                              # ✅ ADD THIS
            await handle_send_nft(update, context, params)
        elif intent == 'send_nft_multi':
            await handle_send_nft_multi(update, context, params)   
        elif intent == 'opt_in':
            await handle_opt_in(update, context, params)
        elif intent == 'opt_out':
            await handle_opt_out(update, context, params)
        elif intent == 'disconnect':
            await handle_disconnect(update, context)
        elif intent == 'balance':
            await handle_balance_check(update, context)
        else:
            await update.message.reply_text("❌ Unsupported action")
    except Exception as e:
        logger.error(f"Error handling message for user {user_id}: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

async def handle_conversation_state(update: Update, context: CallbackContext):
    """Handle conversation states with security validation and message deletion"""
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    message_text = sanitize_input(update.message.text)
    
    if not message_text:
        await delete_message_safely(update, context)
        await update.message.reply_text("❌ Invalid input received.")
        return
    
    # Check for failed attempts
    failed_attempts = context.user_data.get('failed_attempts', 0)
    if failed_attempts >= MAX_PASSWORD_ATTEMPTS:
        log_security_event(user_id, "MAX_ATTEMPTS_EXCEEDED", f"State: {state}")
        context.user_data.clear()
        await delete_message_safely(update, context)
        await update.message.reply_text("❌ Too many failed attempts. Please start over.")
        return
    
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
        await delete_message_safely(update, context)
        await update.message.reply_text("❌ Invalid state. Please start over.")

async def handle_wallet_creation_password(update: Update, context: CallbackContext, password: str):
    """Handle wallet creation with password validation and secure message deletion"""
    user_id = update.effective_user.id
    
    # Delete the password message immediately
    await delete_message_safely(update, context)
    
    # Validate password strength
    if len(password) < 8:
        await update.message.reply_text("❌ Password must be at least 8 characters long.")
        return
    
    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        await update.message.reply_text("❌ Password must contain both letters and numbers.")
        return
    
    try:
        wallet_data = create_wallet(password)
        sessions = load_sessions()
        sessions[str(user_id)] = {
            "address": wallet_data["address"],
            "encrypted_mnemonic": wallet_data["encrypted_mnemonic"],
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        save_sessions(sessions)
        
        log_security_event(user_id, "WALLET_CREATED", f"Address: {wallet_data['address']}")
        
        # Send wallet creation confirmation
        await update.message.reply_text(
            "✅ **Wallet created successfully!**\n\n"
            f"📍 **Address:** `{wallet_data['address']}`\n\n"
            "🔑 **Your mnemonic phrase is below (tap to reveal):**",
            parse_mode="Markdown"
        )
        
        # Send mnemonic as spoiler using MessageEntity
        mnemonic = wallet_data['mnemonic']
        await update.message.reply_text(
            mnemonic,
            entities=[MessageEntity(MessageEntity.SPOILER, 0, len(mnemonic))]
        )
        
        # Send security warning
        await update.message.reply_text(
            "⚠️ **CRITICAL SECURITY WARNING:**\n"
            "• Save this mnemonic phrase immediately\n"
            "• Store it in a secure location offline\n"
            "• Never share it with anyone\n"
            "• This is the ONLY way to recover your wallet\n"
            "• Consider writing it down on paper\n\n"
            "🔐 The mnemonic above is hidden for security. Tap it to reveal.",
            parse_mode="Markdown"
        )
        
        context.user_data.clear()
    except Exception as e:
        logger.error(f"Wallet creation failed for user {user_id}: {e}")
        log_security_event(user_id, "WALLET_CREATION_FAILED", str(e))
        await update.message.reply_text("❌ Failed to create wallet. Please try again.")
        context.user_data.clear()

async def handle_mnemonic_input(update: Update, context: CallbackContext, mnemonic: str):
    """Handle mnemonic input securely with immediate deletion"""
    # Delete the mnemonic message immediately
    await delete_message_safely(update, context)
    
    # Validate mnemonic format
    words = mnemonic.strip().split()
    if len(words) != 25:
        await update.message.reply_text("❌ Invalid mnemonic. Must be exactly 25 words.")
        return
    
    context.user_data['mnemonic'] = mnemonic
    context.user_data['state'] = 'connecting_password'
    await update.message.reply_text(
        "🔒 Please set a password to secure this wallet:\n\n"
        "🔐 Your password will be automatically deleted for security."
    )

async def handle_connection_password(update: Update, context: CallbackContext, password: str):
    """Handle wallet connection password with secure deletion"""
    user_id = update.effective_user.id
    mnemonic = context.user_data.get('mnemonic')
    
    # Delete the password message immediately
    await delete_message_safely(update, context)
    
    try:
        wallet_data = connect_wallet(mnemonic, password)
        sessions = load_sessions()
        sessions[str(user_id)] = {
            "address": wallet_data["address"],
            "encrypted_mnemonic": wallet_data["encrypted_mnemonic"],
            "connected_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        save_sessions(sessions)
        
        log_security_event(user_id, "WALLET_CONNECTED", f"Address: {wallet_data['address']}")
        
        await update.message.reply_text(
            f"✅ **Wallet Connected Successfully!**\n"
            f"📍 Address: `{wallet_data['address']}`\n\n"
            f"🔐 All sensitive information has been securely processed and deleted from chat.",
            parse_mode="Markdown"
        )
        context.user_data.clear()
    except Exception as e:
        logger.error(f"Wallet connection failed for user {user_id}: {e}")
        log_security_event(user_id, "WALLET_CONNECTION_FAILED", str(e))
        await update.message.reply_text("❌ Failed to connect wallet. Please check your mnemonic and try again.")
        context.user_data.clear()

async def handle_send_transaction(update: Update, context: CallbackContext, params: dict):
    """Handle send transaction with security checks"""
    user_id = update.effective_user.id
    
    # Validate session
    if not validate_session(user_id):
        await update.message.reply_text("❌ Please connect a wallet first!")
        return
    
    # Check transaction rate limit
    if not check_user_rate_limit(user_id, "transaction"):
        await update.message.reply_text("⏱️ Transaction rate limit exceeded. Please wait before sending another transaction.")
        return
    
    # Validate parameters
    required_params = ['amount', 'recipient']
    if not all(param in params for param in required_params):
        await update.message.reply_text("❌ Missing transaction details. Example: 'Send 5 ALGO to address'")
        return
    
    # Additional validation
    if not validate_algorand_address(params['recipient']):
        await update.message.reply_text("❌ Invalid recipient address format.")
        return
    
    if params['amount'] <= 0 or params['amount'] > 1000000:
        await update.message.reply_text("❌ Invalid amount. Must be between 0 and 1,000,000 ALGO.")
        return
    
    sessions = load_sessions()
    user_session = sessions.get(str(user_id), {})
    
    try:
        algod_client = get_algod_client()
        result = build_and_send_transaction(
            sender=user_session["address"],
            recipient=params['recipient'],
            amount=params['amount'],
            algod_client=algod_client,
            frontend='telegram'
        )
        
        if result.get('status') == 'awaiting_approval':
            context.user_data['pending_txn'] = result['unsigned_txn']
            context.user_data['state'] = 'transaction_password'
            context.user_data['transaction_type'] = 'send'
            
            log_security_event(user_id, "TRANSACTION_PENDING", f"Amount: {params['amount']} to {params['recipient']}")
            
            await update.message.reply_text(
                f"📝 **Transaction Confirmation Required**\n\n"
                f"💰 Amount: **{params['amount']} ALGO**\n"
                f"📍 To: `{params['recipient']}`\n"
                f"💸 Fee: ~0.001 ALGO\n\n"
                f"🔒 Enter your wallet password to confirm:\n"
                f"🔐 Your password will be automatically deleted for security.",
                parse_mode="Markdown"
            )
        else:
            log_security_event(user_id, "TRANSACTION_COMPLETED", f"TxID: {result.get('txid', 'unknown')}")
            await update.message.reply_text(f"✅ {result['message']}")
    except Exception as e:
        logger.error(f"Transaction failed for user {user_id}: {e}")
        log_security_event(user_id, "TRANSACTION_FAILED", str(e))
        await update.message.reply_text("❌ Transaction failed. Please check your balance and try again.")

async def handle_multi_send_transaction(update: Update, context: CallbackContext, params: dict):
    """Handle multi-recipient send transaction"""
    user_id = update.effective_user.id
    
    # Validate session
    if not validate_session(user_id):
        await update.message.reply_text("❌ Please connect a wallet first!")
        return
    
    # Check transaction rate limit
    if not check_user_rate_limit(user_id, "transaction"):
        await update.message.reply_text("⏱️ Transaction rate limit exceeded.")
        return
    
    # Validate parameters
    if 'recipients' not in params or not params['recipients']:
        await update.message.reply_text("❌ Missing recipient details.")
        return
    
    recipients = params['recipients']
    if len(recipients) < 2:
        await update.message.reply_text("❌ Multi-recipient transfer requires at least 2 recipients.")
        return
    
    # Validate each recipient
    for i, recipient in enumerate(recipients):
        if not validate_algorand_address(recipient['address']):
            await update.message.reply_text(f"❌ Invalid address for recipient #{i+1}")
            return
        if recipient['amount'] <= 0 or recipient['amount'] > 1000000:
            await update.message.reply_text(f"❌ Invalid amount for recipient #{i+1}")
            return
    
    sessions = load_sessions()
    user_session = sessions.get(str(user_id), {})
    
    try:
        algod_client = get_algod_client()
        result = build_and_send_multi_transaction(
            sender=user_session["address"],
            recipients=recipients,
            algod_client=algod_client,
            frontend='telegram'
        )
        
        if result.get('status') == 'awaiting_approval':
            context.user_data['pending_txns'] = result['unsigned_txns']
            context.user_data['state'] = 'transaction_password'
            context.user_data['transaction_type'] = 'multi_send'
            context.user_data['recipients'] = recipients
            
            # Build confirmation message
            message_lines = [
                "📝 **Multi-Recipient Transfer Confirmation**\n",
                f"👥 **Recipients: {len(recipients)}**",
                f"💰 **Total Amount: {result['total_amount']:.6f} ALGO**\n"
            ]
            
            for i, recipient in enumerate(recipients, 1):
                message_lines.append(f"**{i}.** `{recipient['address'][:8]}...{recipient['address'][-8:]}` → **{recipient['amount']:.6f} ALGO**")
            
            message_lines.extend([
                f"\n💸 **Total Fee: ~{len(recipients) * 0.001:.3f} ALGO**",
                "\n🔒 Enter your wallet password to confirm:"
            ])
            
            await update.message.reply_text(
                "\n".join(message_lines),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"✅ {result['message']}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def handle_transaction_password(update: Update, context: CallbackContext, password: str):
    """Handle transaction password with security checks and message deletion"""
    user_id = update.effective_user.id
    
    # Delete the password message immediately
    await delete_message_safely(update, context)

    try:
        # Extract important data BEFORE clearing context
        pending_txn = context.user_data.get('pending_txn')
        pending_txns = context.user_data.get('pending_txns')
        transaction_type = context.user_data.get('transaction_type', 'send')
        asset_id = context.user_data.get('asset_id')
        recipients = context.user_data.get('recipients', [])
        
        # Extract asset_id from transaction if not in context
        if not asset_id and pending_txn and hasattr(pending_txn, 'index'):
            asset_id = pending_txn.index

        if not pending_txn and not pending_txns:
            await update.message.reply_text("❌ No pending transaction found.")
            context.user_data.clear()
            return

        # Clear context AFTER extracting needed data
        context.user_data.clear()

        algod_client = get_algod_client()
        sessions = load_sessions()
        user_address = sessions[str(user_id)]["address"]

        # Handle different transaction types
        if transaction_type == 'opt_in':
            signed_txn = sign_transaction(pending_txn, password=password, frontend='telegram')
            txid = algod_client.send_transaction(signed_txn)
            log_security_event(user_id, "ASSET_OPT_IN", f"Asset: {asset_id}, TxID: {txid}")
            await update.message.reply_text(f"✅ Opt-in successful! TxID: `{txid}`", parse_mode="Markdown")
            
        elif transaction_type == 'opt_out':
            # PROPER OPT-OUT VALIDATION WITH RETRY LOGIC
            asset_holding = None
            
            # Retry up to 3 times with 2-second delay (for indexer sync after recent opt-in)
            for attempt in range(3):
                try:
                    account_info = algod_client.account_info(user_address)
                    asset_holding = next(
                        (asset for asset in account_info.get('assets', []) 
                         if asset['asset-id'] == asset_id), 
                        None
                    )
                    if asset_holding:
                        break
                    if attempt < 2:  # Don't sleep on last attempt
                        time.sleep(2)
                except Exception as e:
                    logger.error(f"Account info check failed for user {user_id}, attempt {attempt + 1}: {e}")
                    if attempt < 2:
                        time.sleep(2)

            if not asset_holding:
                await update.message.reply_text(f"❌ You are not opted into asset {asset_id}")
                return

            if asset_holding['amount'] > 0:
                await update.message.reply_text(
                    f"❌ Cannot opt-out: You hold {asset_holding['amount']} units of asset {asset_id}.\n"
                    f"Transfer them first before opting out."
                )
                return

            # Proceed with opt-out
            signed_txn = sign_transaction(pending_txn, password=password, frontend='telegram')
            txid = algod_client.send_transaction(signed_txn)
            log_security_event(user_id, "ASSET_OPT_OUT", f"Asset: {asset_id}, TxID: {txid}")
            await update.message.reply_text(
                f"✅ Opt-out successful!\n"
                f"🆔 Asset ID: {asset_id}\n"
                f"📄 TxID: `{txid}`",
                parse_mode="Markdown"
            )
            
        elif transaction_type == 'multi_send':
            # Handle multi-recipient ALGO transactions
            signed_txns = []
            for txn in pending_txns:
                signed_txn = sign_transaction(txn, password=password, frontend='telegram')
                signed_txns.append(signed_txn)
            
            txid = algod_client.send_transactions(signed_txns)
            total_amount = sum(r['amount'] for r in recipients)
            log_security_event(user_id, "MULTI_SEND_COMPLETED", f"Recipients: {len(recipients)}, Total: {total_amount} ALGO")
            
            await update.message.reply_text(
                f"✅ **Multi-Recipient Transfer Successful!**\n"
                f"👥 **{len(recipients)} recipients**\n"
                f"💰 **Total: {total_amount:.6f} ALGO**\n"
                f"📄 **Group TxID:** `{txid}`",
                parse_mode="Markdown"
            )

        elif transaction_type == 'nft_transfer':
            # Handle single NFT transfer
            # Verify sender ownership
            account_info = algod_client.account_info(user_address)
            owns_nft = any(
                a['asset-id'] == asset_id and a['amount'] > 0
                for a in account_info.get('assets', [])
            )
            if not owns_nft:
                await update.message.reply_text(f"❌ You don't own NFT {asset_id}")
                return

            # Verify recipient opted-in
            recipient = pending_txn.receiver
            try:
                recipient_info = algod_client.account_info(recipient)
                recipient_opted_in = any(a['asset-id'] == asset_id for a in recipient_info.get('assets', []))
            except Exception:
                recipient_opted_in = False

            if not recipient_opted_in:
                await update.message.reply_text(
                    f"❌ Recipient must opt-in first!\n"
                    f"Ask them to use: 'Opt-in to asset {asset_id}'"
                )
                return

            signed_txn = sign_transaction(pending_txn, password=password, frontend='telegram')
            txid = algod_client.send_transaction(signed_txn)
            log_security_event(user_id, "NFT_TRANSFERRED", f"Asset ID: {asset_id}, TxID: {txid}")
            await update.message.reply_text(
                f"✅ **NFT Transferred!**\n"
                f"🆔 Asset ID: `{asset_id}`\n"
                f"👤 To: `{recipient[:8]}...`\n"
                f"📄 TxID: `{txid}`",
                parse_mode="Markdown"
            )

        elif transaction_type == 'nft_multi_transfer':
            # Handle multi-recipient NFT transfer
            signed_txns = []
            for txn in pending_txns:
                signed_txn = sign_transaction(txn, password=password, frontend='telegram')
                signed_txns.append(signed_txn)
            
            txid = algod_client.send_transactions(signed_txns)
            log_security_event(user_id, "NFT_MULTI_TRANSFER", f"Asset ID: {asset_id}, Recipients: {len(recipients)}")
            await update.message.reply_text(
                f"✅ **Multi-NFT Transfer Complete!**\n"
                f"🆔 Asset ID: `{asset_id}`\n"
                f"👥 Recipients: {len(recipients)}\n"
                f"📄 Group TxID: `{txid}`",
                parse_mode="Markdown"
            )
            
        elif transaction_type == 'nft':
            signed_txn = sign_transaction(pending_txn, password=password, frontend='telegram')
            txid = algod_client.send_transaction(signed_txn)
            asset_id = get_asset_id_from_txid(algod_client, txid)
            log_security_event(user_id, "NFT_CREATED", f"TxID: {txid}")
            await update.message.reply_text(
                f"✅ **NFT Created Successfully!**\n"
                f"🆔 Asset ID: `{asset_id}`\n"
                f"📄 Transaction ID: `{txid}`",
                parse_mode="Markdown"
            )
            
        else:  # Default case for regular ALGO transactions
            signed_txn = sign_transaction(pending_txn, password=password, frontend='telegram')
            txid = algod_client.send_transaction(signed_txn)
            log_security_event(user_id, "TRANSACTION_SIGNED", f"TxID: {txid}")
            await update.message.reply_text(
                f"✅ **Transaction Successful!**\n"
                f"📄 Transaction ID: `{txid}`",
                f"⏳ Asset ID will be available once confirmed.",
                parse_mode="Markdown"
            )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Transaction failed for user {user_id}: {error_msg}")
        
        # Handle specific Algorand errors
        if "already in ledger" in error_msg:
            await update.message.reply_text("✅ Transaction already completed successfully.")
        elif "must optin" in error_msg.lower():
            await update.message.reply_text(
                f"❌ Recipient not opted in to asset {asset_id}!\n"
                f"Ask them to use: 'Opt-in to asset {asset_id}'"
            )
        elif "cannot close asset ID in allocating account" in error_msg:
            await update.message.reply_text(f"❌ Cannot opt-out of asset {asset_id}: You may still have a balance.")
        elif "asset does not exist" in error_msg:
            await update.message.reply_text(f"❌ Asset {asset_id} does not exist.")
        else:
            failed_attempts = context.user_data.get('failed_attempts', 0) + 1
            if failed_attempts >= MAX_PASSWORD_ATTEMPTS:
                context.user_data.clear()
                await update.message.reply_text("❌ Too many failed attempts. Session reset.")
            else:
                context.user_data['failed_attempts'] = failed_attempts
                remaining = MAX_PASSWORD_ATTEMPTS - failed_attempts
                await update.message.reply_text(f"❌ Incorrect password. {remaining} attempts remaining.")
    
async def handle_nft_creation(update: Update, context: CallbackContext, params: dict):
    """Handle NFT creation with video/image support and enhanced security"""
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    # Validate session and parameters
    if not validate_session(user_id):
        await update.message.reply_text("❌ Please connect a wallet first!")
        return

    if 'name' not in params or not params['name']:
        await update.message.reply_text("❌ Missing NFT name. Example: 'Create NFT named Dragon'")
        return

    nft_name = sanitize_input(params['name'])
    if not 1 <= len(nft_name) <= 50:
        await update.message.reply_text("❌ NFT name must be 1-50 characters long.")
        return

    # Media handling
    media_url = None
    media_type = None
    media_path = None
    
    # Check for video first
    if 'nft_video' in context.user_data:
        media_type = 'video'
        media_path = context.user_data['nft_video']
    elif 'nft_image' in context.user_data:
        media_type = 'image'
        media_path = context.user_data['nft_image']
        
    try:
        # Process media if exists
        if media_path:
            try:
                # Upload to IPFS
                media_url = upload_to_ipfs(media_path)
                
                # Cleanup temp file
                os.unlink(media_path)
                del context.user_data[f'nft_{media_type}']
                
                # Log media upload
                logger.info(f"User {user_id} uploaded {media_type} to IPFS: {media_url}")
                log_security_event(user_id, "MEDIA_UPLOADED", f"Type: {media_type}, URL: {media_url}")
                
            except Exception as e:
                await update.message.reply_text(f"❌ {media_type.capitalize()} processing error: {str(e)}")
                logger.error(f"{media_type.capitalize()} handling failed for user {user_id}: {e}")
                return

        # Create metadata
        metadata = {
            "name": nft_name,
            "description": sanitize_input(params.get('description', "")),
            "media_type": media_type,
            "media_url": media_url,
            "creator": sessions[str(user_id)]["address"]
        }

        # Create NFT transaction
        algod_client = get_algod_client()
        result = create_nft(
            name=nft_name,
            unit_name=generate_unit_name(nft_name),
            total_supply=params.get('supply', 1),
            description=metadata["description"],
            algod_client=algod_client,
            sender=sessions[str(user_id)]["address"],
            frontend='telegram',
            url=media_url
        )

        # Handle transaction approval flow
        if isinstance(result, dict) and result.get('status') == 'awaiting_approval':
            context.user_data.update({
                'pending_txn': result['unsigned_txn'],
                'state': 'transaction_password',
                'transaction_type': 'nft'
            })
            
            # Build confirmation message
            message = [
                f"🎨 **NFT Creation Confirmation**",
                f"📛 Name: {nft_name}",
                f"📊 Supply: {params.get('supply', 1)}",
                f"📝 Description: {metadata['description'] or 'None'}"
            ]
            
            if media_url:
                message.append(f"🌄 Media: {media_url} ({media_type})")
                
            message.append("💸 Fee: ~0.001 ALGO\n\n🔒 Enter your wallet password:")
            
            await update.message.reply_text(
                "\n".join(message),
                parse_mode="Markdown"
            )
            
        else:
            # Direct success case with asset ID from transaction builder
            log_security_event(user_id, "NFT_CREATED", f"Asset ID: {result.get('asset_id')}")
            response_message = [
                f"✅ **NFT Created Successfully!**",
                f"🆔 Asset ID: `{result.get('asset_id')}`",
                f"📄 Transaction ID: `{result.get('txid')}`"
            ]
            if media_url:
                response_message.append(f"🔗 Media: {media_url}")
                
            await update.message.reply_text(
                "\n".join(response_message),
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"NFT creation failed for user {user_id}: {e}")
        log_security_event(user_id, "NFT_CREATION_FAILED", str(e))
        await update.message.reply_text("❌ Failed to create NFT. Please try again.")

async def handle_photo(update: Update, context: CallbackContext):
    """Handle image uploads for NFT creation with caption support"""
    user_id = update.effective_user.id
    try:
        # Get the image
        photo_file = await update.message.photo[-1].get_file()
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            await photo_file.download_to_drive(temp_file.name)
            context.user_data['nft_image'] = temp_file.name
        
        # Check if user sent a caption with the image
        caption = update.message.caption
        if caption:
            print(f"DEBUG: Original caption: '{caption}'")  # Debug log
            
            # Try to parse the caption as an NFT intent
            sanitized_caption = sanitize_input(caption)
            print(f"DEBUG: Sanitized caption: '{sanitized_caption}'")  # Debug log
            
            intent_parser = AIIntentParser()
            parsed = intent_parser.parse(sanitized_caption)
            print(f"DEBUG: AI parsed result: {parsed}")  # Debug log
            
            # If caption contains valid NFT intent, process immediately
            if parsed and parsed.get('intent') == 'create_nft':
                params = parsed.get('parameters', {})
                print(f"DEBUG: Extracted parameters: {params}")  # Debug log
                await handle_nft_creation(update, context, params)
                return ConversationHandler.END
            
            # If caption doesn't contain valid NFT intent, try fallback parsing
            fallback_parsed = parse_nft_command_fallback(sanitized_caption)
            print(f"DEBUG: Fallback parsed result: {fallback_parsed}")  # Debug log
            
            if fallback_parsed:
                params = fallback_parsed.get('parameters', {})
                print(f"DEBUG: Fallback extracted parameters: {params}")  # Debug log
                await handle_nft_creation(update, context, params)
                return ConversationHandler.END
            
            # Caption exists but doesn't contain valid NFT intent
            await update.message.reply_text(
                f"📸 Image received! However, I couldn't understand your NFT description: '{caption}'\n"
                "Please describe your NFT:\n"
                "Example: 'Create NFT named Dragon with supply 10'"
            )
        else:
            # No caption provided, ask for description
            await update.message.reply_text(
                "📸 Image received! Describe your NFT:\n"
                "Example: 'Create NFT named Dragon with this image'"
            )
        
        return IMAGE_HANDLING
        
    except Exception as e:
        logger.error(f"Image handling failed: {e}")
        await update.message.reply_text("❌ Failed to process image")
        return ConversationHandler.END

async def handle_image_state(update: Update, context: CallbackContext):
    """Handle NFT creation with image"""
    user_input = sanitize_input(update.message.text)
    user_id = update.effective_user.id
    try:
        intent_parser = AIIntentParser()
        parsed = intent_parser.parse(user_input)
        if not parsed or parsed.get('intent') != 'create_nft':
            await update.message.reply_text("❌ Invalid NFT command")
            return ConversationHandler.END
        image_path = context.user_data['nft_image']
        ipfs_url = upload_to_ipfs(image_path)
        os.unlink(image_path)
        params = parsed.get('parameters', {})
        params['image_url'] = ipfs_url
        await handle_nft_creation(update, context, params)
        del context.user_data['nft_image']
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Image NFT failed: {e}")
        await update.message.reply_text("❌ NFT creation failed")
        return ConversationHandler.END

async def handle_video(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        video_file = await update.message.video.get_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            await video_file.download_to_drive(temp_file.name)
            context.user_data['nft_video'] = temp_file.name

        caption = update.message.caption
        if caption:
            # Try to parse the caption as an NFT intent
            sanitized_caption = sanitize_input(caption)
            intent_parser = AIIntentParser()
            parsed = intent_parser.parse(sanitized_caption)
            if parsed and parsed.get('intent') == 'create_nft':
                params = parsed.get('parameters', {})
                params['video_path'] = context.user_data['nft_video']
                await handle_nft_creation(update, context, params)
                return ConversationHandler.END
            # Fallback parsing...
        else:
            await update.message.reply_text(
                "🎥 Video received! Now describe your NFT:\n"
                "Example: 'Create NFT named Dance with this video'"
            )
            return IMAGE_HANDLING
    except Exception as e:
        logger.error(f"Video handling failed: {e}")
        await update.message.reply_text("❌ Failed to process video")
        return ConversationHandler.END
    
async def handle_send_nft(update: Update, context: CallbackContext, params: dict):
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    # Validate session
    if str(user_id) not in sessions:
        await update.message.reply_text("❌ Connect wallet first!")
        return
        
    # Validate parameters
    if 'asset_id' not in params or 'recipient' not in params:
        await update.message.reply_text("❌ Missing NFT ID or recipient")
        return
        
    try:
        asset_id = int(params['asset_id'])
        recipient = params['recipient']
        
        if not validate_algorand_address(recipient):
            await update.message.reply_text("❌ Invalid recipient address")
            return
            
        algod_client = get_algod_client()
        result = send_nft(
            sender=sessions[str(user_id)]["address"],
            asset_id=asset_id,
            recipient=recipient,
            algod_client=algod_client,
            frontend='telegram'
        )
        
        if result.get('status') == 'awaiting_approval':
            context.user_data.update({
                'pending_txn': result['unsigned_txn'],
                'state': 'transaction_password',
                'transaction_type': 'nft_transfer'
            })
            
            await update.message.reply_text(
                f"📦 **NFT Transfer Confirmation**\n\n"
                f"🆔 Asset ID: {asset_id}\n"
                f"👤 Recipient: {recipient}\n"
                f"💸 Fee: ~0.001 ALGO\n\n"
                f"🔒 Enter your wallet password:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"✅ NFT transferred! TXID: {result['txid']}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def handle_send_nft_multi(update: Update, context: CallbackContext, params: dict):
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    if str(user_id) not in sessions:
        await update.message.reply_text("❌ Connect wallet first!")
        return
        
    try:
        asset_id = int(params['asset_id'])
        recipients = params['recipients']
        
        # Validate recipients
        valid_recipients = []
        for addr in recipients:
            if validate_algorand_address(addr):
                valid_recipients.append(addr)
            else:
                await update.message.reply_text(f"❌ Skipping invalid address: {addr}")
                
        if not valid_recipients:
            await update.message.reply_text("❌ No valid recipients")
            return
            
        algod_client = get_algod_client()
        result = send_nft_multi(
            sender=sessions[str(user_id)]["address"],
            asset_id=asset_id,
            recipients=valid_recipients,
            algod_client=algod_client,
            frontend='telegram'
        )
        
        if result.get('status') == 'awaiting_approval':
            context.user_data.update({
                'pending_txns': result['unsigned_txns'],
                'state': 'transaction_password',
                'transaction_type': 'nft_multi_transfer'
            })
            
            message = [
                f"📦 **Multi-NFT Transfer Confirmation**",
                f"🆔 Asset ID: {asset_id}",
                f"👥 Recipients: {len(valid_recipients)}",
                f"💸 Total Fee: ~{len(valid_recipients)*0.001:.3f} ALGO\n"
            ]
            
            for i, addr in enumerate(valid_recipients[:3]):  # Show first 3
                message.append(f"`{addr[:8]}...{addr[-8:]}`")
                
            if len(valid_recipients) > 3:
                message.append(f"...and {len(valid_recipients)-3} more")
                
            message.append("\n🔒 Enter your wallet password:")
            
            await update.message.reply_text("\n".join(message), parse_mode="Markdown")
            
        else:
            await update.message.reply_text(f"✅ NFTs transferred! TXID: {result['txid']}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        
async def debug_nft_transfer(update: Update, context: CallbackContext, asset_id: int, recipient: str):
    """Debug NFT transfer issues"""
    user_id = update.effective_user.id
    sessions = load_sessions()
    user_address = sessions[str(user_id)]["address"]
    
    try:
        algod_client = get_algod_client()
        
        # Check sender account
        sender_info = algod_client.account_info(user_address)
        sender_owns = False
        for asset in sender_info.get('assets', []):
            if asset['asset-id'] == asset_id:
                sender_owns = asset['amount'] > 0
                break
        
        # Check recipient account
        try:
            recipient_info = algod_client.account_info(recipient)
            recipient_opted_in = any(asset['asset-id'] == asset_id for asset in recipient_info.get('assets', []))
        except:
            recipient_opted_in = False
        
        # Check asset info
        try:
            asset_info = algod_client.asset_info(asset_id)
            asset_exists = True
        except:
            asset_exists = False
        
        debug_msg = [
            f"🔍 **NFT Transfer Debug**",
            f"🆔 Asset ID: {asset_id}",
            f"📤 You own NFT: {'✅' if sender_owns else '❌'}",
            f"📥 Recipient opted in: {'✅' if recipient_opted_in else '❌'}",
            f"🎨 Asset exists: {'✅' if asset_exists else '❌'}"
        ]
        
        if not recipient_opted_in:
            debug_msg.append(f"\n💡 **Solution:** Ask recipient to opt-in first:\n`Opt-in to asset {asset_id}`")
        
        await update.message.reply_text("\n".join(debug_msg), parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Debug failed: {str(e)}")

async def handle_opt_in(update: Update, context: CallbackContext, params: dict):
    user_id = update.effective_user.id
    if not validate_session(user_id):
        await update.message.reply_text("❌ Please connect a wallet first!")
        return
    sessions = load_sessions()
    user_session = sessions.get(str(user_id), {})
    try:
        asset_id = int(params['asset_id'])
    except Exception:
        await update.message.reply_text("❌ Invalid asset ID. Please provide a valid number.")
        return
    try:
        algod_client = get_algod_client()
        result = opt_in_to_asset(
            sender=user_session["address"],
            asset_id=asset_id,
            algod_client=algod_client,
            frontend='telegram'
        )
        if result.get('status') == 'awaiting_approval':
            context.user_data['pending_txn'] = result['unsigned_txn']
            context.user_data['state'] = 'transaction_password'
            context.user_data['transaction_type'] = 'opt_in'
            await update.message.reply_text(
                f"🔗 **Opt-In Confirmation**\n\n"
                f"🆔 Asset ID: {asset_id}\n"
                f"💸 Fee: ~0.001 ALGO\n\n"
                f"🔒 Enter your wallet password to confirm opt-in:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"✅ Successfully opted in to asset {asset_id}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Opt-in failed: {str(e)}")

async def handle_opt_out(update: Update, context: CallbackContext, params: dict):
    user_id = update.effective_user.id
    if not validate_session(user_id):
        await update.message.reply_text("❌ Please connect a wallet first!")
        return
    sessions = load_sessions()
    user_session = sessions.get(str(user_id), {})
    try:
        asset_id = int(params['asset_id'])
    except Exception:
        await update.message.reply_text("❌ Invalid asset ID. Please provide a valid number.")
        return
    try:
        algod_client = get_algod_client()
        result = opt_out_of_asset(
            sender=user_session["address"],
            asset_id=asset_id,
            algod_client=algod_client,
            frontend='telegram'
        )
        if result.get('status') == 'awaiting_approval':
            context.user_data['pending_txn'] = result['unsigned_txn']
            context.user_data['state'] = 'transaction_password'
            context.user_data['transaction_type'] = 'opt_out'
            await update.message.reply_text(
                f"🔗 **Opt-Out Confirmation**\n\n"
                f"🆔 Asset ID: {asset_id}\n"
                f"💸 Fee: ~0.001 ALGO\n\n"
                f"🔒 Enter your wallet password to confirm opt-out:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"✅ Successfully opted out of asset {asset_id}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Opt-out failed: {str(e)}")


async def handle_balance_check(update: Update, context: CallbackContext):
    """Check wallet balance securely"""
    user_id = update.effective_user.id
    
    if not validate_session(user_id):
        await update.message.reply_text("❌ Please connect a wallet first!")
        return
    
    sessions = load_sessions()
    user_session = sessions.get(str(user_id), {})
    
    try:
        algod_client = get_algod_client()
        account_info = algod_client.account_info(user_session["address"])
        balance = account_info.get("amount", 0) / 1_000_000
        
        log_security_event(user_id, "BALANCE_CHECKED")
        
        await update.message.reply_text(
            f"💰 **Wallet Balance**\n"
            f"Balance: **{balance:.6f} ALGO**",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Balance check failed for user {user_id}: {e}")
        await update.message.reply_text("❌ Failed to check balance. Please try again.")

async def handle_disconnect(update: Update, context: CallbackContext):
    """Disconnect wallet securely"""
    user_id = update.effective_user.id
    sessions = load_sessions()
    
    if str(user_id) in sessions:
        log_security_event(user_id, "WALLET_DISCONNECTED")
        del sessions[str(user_id)]
        save_sessions(sessions)
    
    context.user_data.clear()
    await update.message.reply_text("✅ Wallet disconnected securely")
    
async def cancel(update: Update, context: CallbackContext):
    """Cancel current conversation"""
    exit_keyboard = ReplyKeyboardMarkup(
    [["❌ Cancel", "🏠 Main Menu"]], 
    resize_keyboard=True, 
    one_time_keyboard=True
)
    await update.message.reply_text(
        "Please enter your mnemonic:",
        reply_markup=exit_keyboard
    )
    await update.message.reply_text(
        "❌ Operation cancelled. Type /start to see available commands.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

def main():
    """Start the bot with security logging"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    logger.info("Starting Algo-Intent Bot with enhanced security")
    security_logger.info("Bot started with public access and message security enabled")
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add cancel handler first (highest priority)
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Add start handler
    application.add_handler(CommandHandler("start", start))
    
    # Add media handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # Conversation handler with proper fallbacks
    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            IMAGE_HANDLING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_image_state)],
            WALLET_CONNECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mnemonic_input)],
            CREATING_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_creation_password)],
            'transaction_password': [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_conversation_state)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),          # /cancel exits conversation
            CommandHandler("start", start),            # /start exits conversation  
            MessageHandler(filters.COMMAND, cancel)   # ANY command exits conversation
        ],
        allow_reentry=True
    )
    
    application.add_handler(conversation_handler)
    
    logger.info("🤖 Secure Bot started! Ready for public use with message security.")
    application.run_polling()

# Add this cancel function before main()
async def cancel(update: Update, context: CallbackContext):
    """Cancel current conversation and return to main menu"""
    await update.message.reply_text(
        "❌ Operation cancelled.\n"
        "Type /start to see available commands.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

if __name__ == "__main__":
    main()
