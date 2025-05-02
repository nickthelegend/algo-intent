import os
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk.encoding import is_valid_address
import ssl
# Disable SSL verification (not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()

ALGOD_ADDRESS = os.getenv('ALGOD_ADDRESS', 'https://testnet-api.algonode.cloud')
ALGOD_PORT = os.getenv('ALGOD_PORT', '443')
ALGOD_TOKEN = os.getenv('ALGOD_TOKEN', 'a' * 64)
SENDER_ADDRESS = os.getenv('SENDER_ADDRESS', '')
SENDER_MNEMONIC = os.getenv('SENDER_MNEMONIC', '')

def get_algod_client():
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

def validate_address(address):
    return is_valid_address(address)

def text_to_number(text):
    numbers = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
        'hundred': 100, 'thousand': 1000
    }
    text = text.lower().replace('-', ' ')
    parts = text.split()
    total = 0
    current = 0
    for part in parts:
        if part not in numbers:
            return None
        val = numbers[part]
        if val == 100 or val == 1000:
            if current == 0:
                current = 1
            current *= val
        else:
            current += val
    total += current
    return total

def normalize_token_name(token_name):
    token_name = token_name.lower()
    if token_name in ['algo', 'algos', 'algorand', 'algorand token', 'algorand tokens']:
        return 'ALGO'
    return token_name.upper()

def check_account_balance(address, amount, client):
    try:
        account_info = client.account_info(address)
        balance = account_info.get('amount', 0) / 1_000_000
        return balance >= amount, balance
    except Exception:
        return False, 0

def generate_unit_name(name: str) -> str:
    initials = ''.join(word[0] for word in name.split() if word).upper()
    return initials[:8] if initials else 'NFT'

def normalize_number(input_str: str) -> int:
    input_str = input_str.strip().lower()
    if input_str.isdigit():
        return int(input_str)
    n = text_to_number(input_str)
    return n if n is not None else 1
