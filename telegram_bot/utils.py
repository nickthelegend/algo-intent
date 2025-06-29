import os
import re
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk.encoding import is_valid_address
import ssl

# Disable SSL verification (not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()
# Disable SSL verification (not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context

ALGOD_ADDRESS = os.getenv('ALGOD_ADDRESS', 'https://testnet-api.algonode.cloud')
ALGOD_PORT = os.getenv('ALGOD_PORT', '443')
ALGOD_TOKEN = os.getenv('ALGOD_TOKEN', 'a' * 64)

def get_algod_client():
    try:
        return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
    except NameError:
        raise ImportError("algosdk is required for this function. Install with: pip install py-algorand-sdk")

def validate_address(address):
    return is_valid_address(address)

def text_to_number(text):
    """
    Convert text representation of numbers to actual numbers
    Handles: 'five', 'twenty five', 'one hundred', 'zero point five', etc.
    """
    if not text or not isinstance(text, str):
        return None
        
    # Handle decimal numbers with 'point'
    numbers = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
        'hundred': 100, 'thousand': 1000, 'million': 1000000, 'billion': 1000000000,
        'point': '.'  # For decimal handling
    }
    
    # Handle hyphenated numbers like "twenty-five"
    text = text.lower().replace('-', ' ')
    
    # Handle "and" in numbers like "one hundred and five"
    text = text.replace(' and ', ' ')
    
    parts = text.split()
    total = 0
    current = 0
    decimal_part = False
    decimal_str = ''

    for part in parts:
        if part not in numbers:
            return None
        val = numbers[part]
        if val == '.':
            decimal_part = True
            continue
        if not decimal_part:
            if val in [100, 1000, 1000000, 1000000000]:
                if current == 0:
                    current = 1
                current *= val
                # If this is the last multiplier in a sequence, add to total
                if parts.index(part) == len(parts) - 1 or numbers[parts[parts.index(part) + 1]] < 100:
                    total += current
                    current = 0
            else:
                current += val
        else:
            # Decimal part: append digits as string
            decimal_str += str(val)
    total += current
    if decimal_part:
        try:
            decimal_value = float('0.' + decimal_str)
            total += decimal_value
        except:
            return None
    return total

def normalize_token_name(token_name):
    """
    Normalize various token name formats to standard format
    Expanded to handle more variations of Algorand token names
    """
    if not token_name:
        return None
        
    token_name = token_name.lower().strip()
    
    # Algorand native token variations
    algo_variations = [
        'algo', 'algos', 'algorand', 'algorand token', 'algorand tokens',
        'native token', 'native algo', 'native algorand', 'algo token',
        'algos token', 'algos tokens', 'algo native token', 'native algo token',
        'alg', 'algs', 'algorands', 'algorand coin', 'algo coin',
        # Additional multi-word variations
        'native algorand token', 'native algorand tokens',
        'algorand native token', 'algorand native tokens',
        'native algo tokens', 'algo native tokens',
        'native token of algorand', 'algorand native currency',
        'algo cryptocurrency', 'algorand cryptocurrency'
    ]
    
    if token_name in algo_variations:
        return 'ALGO'
    
    # Check if token name contains "algo" or "algorand" as part of a longer phrase
    if any(variation in token_name for variation in ['algo', 'algorand']):
        return 'ALGO'
    
    # Common ASAs could be added here
    asa_mapping = {
        'usdc': 'USDC',
        'usdt': 'USDT',
        'tether': 'USDT',
        'usd coin': 'USDC',
        'dai': 'DAI',
        'planet': 'PLANET',
        'planets': 'PLANET',
        'planetwatch': 'PLANET',
        'gard': 'GARD',
        'gardian': 'GARD'
    }
    
    if token_name in asa_mapping:
        return asa_mapping[token_name]
    
    # Default to uppercase for other tokens
    return token_name.upper()

def check_account_balance(address, amount, client, token='ALGO'):
    """
    Check if account has sufficient balance for a transaction
    Now supports checking both ALGO and ASA balances
    """
    try:
        account_info = client.account_info(address)
        
        if token == 'ALGO':
            # Check ALGO balance
            balance = account_info.get('amount', 0) / 1_000_000
            return balance >= amount, balance
        else:
            # Check ASA balance
            assets = account_info.get('assets', [])
            for asset in assets:
                # This would need to be expanded to look up ASA IDs by name
                # For now, just a placeholder
                if asset.get('asset-id') == 0:  # Replace with actual ASA ID lookup
                    balance = asset.get('amount', 0) / 1_000_000  # Adjust decimals based on asset
                    return balance >= amount, balance
            return False, 0
    except Exception as e:
        return False, 0

def generate_unit_name(name: str) -> str:
    """Generate a unit name from a full name (e.g., 'Blue Dragon' -> 'BD')"""
    initials = ''.join(word[0] for word in name.split() if word).upper()
    return initials[:8] if initials else 'NFT'

def normalize_number(input_str: str) -> int:
    """Convert string numbers (text or digits) to integers"""
    if not input_str:
        return 1
        
    input_str = input_str.strip().lower()
    
    # If it's already a digit
    if input_str.isdigit():
        return int(input_str)
    
    # Try to convert text to number
    n = text_to_number(input_str)
    return n if n is not None else 1

def parse_address(text):
    """Extract Algorand address from text"""
    # Look for standard Algorand address format (58 characters, base32)
    pattern = r'[A-Z2-7]{58}'
    match = re.search(pattern, text)
    if match:
        address = match.group(0)
        if validate_address(address):
            return address
    return None

def format_algo_amount(amount):
    """Format ALGO amount with proper decimal places"""
    if amount >= 1000000:
        return f"{amount/1000000:.2f}M ALGO"
    elif amount >= 1000:
        return f"{amount/1000:.2f}K ALGO"
    else:
        return f"{amount:.6f} ALGO"

def is_valid_nft_name(name):
    """Check if a name is valid for an NFT"""
    if not name or len(name) < 1:
        return False
    # NFT names should be alphanumeric with spaces
    return bool(re.match(r'^[a-zA-Z0-9\s]+$', name))

def extract_intent_components(text):
    """
    Extract all components of a transaction intent from natural language
    Returns dict with action, amount, token, recipient
    """
    # Extract action (send, transfer, etc.)
    action_pattern = r'\b(send|transfer|move|pay|give)\b'
    action_match = re.search(action_pattern, text, re.IGNORECASE)
    action = action_match.group(1).lower() if action_match else None
    
    # Extract recipient address
    recipient = parse_address(text)
    
    # Extract amount and token
    amount, token = extract_token_info(text)
    
    # If we couldn't extract a token but found an amount, default to ALGO
    if amount is not None and token is None:
        token = 'ALGO'
    
    return {
        'action': action,
        'amount': amount,
        'token': token,
        'recipient': recipient
    }

def extract_token_info(text):
    """
    Extract token name and amount from natural language text
    Returns tuple of (amount, token_name)
    """
    # More flexible pattern to match longer token names
    # This will capture phrases like "native algorand token" or "five algo native tokens"
    pattern = r'(\d+(?:\.\d+)?|[a-zA-Z\s-]+)\s+((?:native\s+)?(?:algo|algos|algorand|usdc|usdt|dai|gard|planet)(?:\s+(?:native\s+)?(?:token|tokens|coin|cryptocurrency))?(?:\s+(?:of\s+)?(?:algorand))?)'
    
    match = re.search(pattern, text, re.IGNORECASE)
    
    if not match:
        return None, None
    
    amount_text, token_text = match.groups()
    
    # Clean up amount text (remove trailing spaces that might have been captured)
    amount_text = amount_text.strip()
    
    # Convert amount to number
    if amount_text.replace('.', '').isdigit():
        amount = float(amount_text)
    else:
        amount = text_to_number(amount_text)
    
    # Normalize token name
    token = normalize_token_name(token_text)
    
    return amount, token
