import re
from utils import text_to_number, normalize_token_name, normalize_number

def parse_intent(user_input):
    pattern = re.compile(
        r"(?P<action>send|transfer)\s+(?P<amount>\d*\.?\d+|[a-zA-Z\s-]+)\s+(?P<token>algo|algos|algorand|algorand token|algorand tokens)\s+to\s+(?P<address>[A-Z0-9]{58})",
        re.IGNORECASE
    )
    match = pattern.search(user_input)
    if not match:
        return None
    intent = match.groupdict()
    intent['token'] = normalize_token_name(intent['token'])
    amount = intent['amount'].strip()
    if not any(c.isdigit() for c in amount):
        numeric_amount = text_to_number(amount)
        if numeric_amount is None:
            return None
        intent['amount'] = numeric_amount
    else:
        try:
            intent['amount'] = float(amount)
        except ValueError:
            return None
    intent['action'] = intent['action'].lower()
    return {
        'action': intent['action'],
        'amount': intent['amount'],
        'token': intent['token'],
        'recipient': intent['address']
    }

def parse_nft_intent(user_input: str):
    pattern = re.compile(
        r"(create|mint)\s+(an?\s+)?nft(\s+(named|called))?\s*(?P<name>[a-zA-Z0-9 ]+)?"
        r"(\s+with\s+description\s+(?P<description>[^,]+))?"
        r"(\s+(with\s+)?(supply|copies?|quantity)\s+(?P<total_supply>[a-zA-Z0-9 ]+))?",
        re.IGNORECASE
    )
    match = pattern.search(user_input)
    if not match:
        return None
    name = match.group('name')
    description = match.group('description')
    total_supply = match.group('total_supply')
    if name:
        name = name.strip()
    if description:
        description = description.strip()
    if total_supply:
        total_supply = normalize_number(total_supply.strip())
    return {
        "name": name,
        "description": description,
        "total_supply": total_supply
    }
