import re
from utils import (
    text_to_number, 
    normalize_token_name, 
    normalize_number, 
    extract_token_info, 
    extract_intent_components,
    parse_address
)

def parse_intent(user_input):
    """
    Parse natural language intent for sending tokens
    Improved to handle text numbers with multi-word token descriptions
    """
    # First try the extract_intent_components approach
    components = extract_intent_components(user_input)
    if (components['action'] and components['amount'] is not None and 
            components['token'] and components['recipient']):
        return {
            'action': components['action'],
            'amount': components['amount'],
            'token': components['token'],
            'recipient': components['recipient']
        }
    
    # If that fails, use a more targeted approach
    
    # Extract action and address first (these are easier to identify)
    action_pattern = r'\b(send|transfer|move|pay|give)\b'
    action_match = re.search(action_pattern, user_input, re.IGNORECASE)
    if not action_match:
        return None
    action = action_match.group(1).lower()
    
    # Extract address
    address = parse_address(user_input)
    if not address:
        return None
    
    # Now extract the middle part between action and "to address"
    to_address_part = f"to {address}"
    middle_text = user_input[user_input.lower().find(action.lower()) + len(action):user_input.lower().find(to_address_part.lower())]
    middle_text = middle_text.strip()
    
    # Define number words that might appear in text-based numbers
    number_words = [
        'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen',
        'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety',
        'hundred', 'thousand', 'million', 'point'
    ]
    
    # Define token words that might appear in token descriptions
    token_words = [
        'algo', 'algos', 'algorand', 'token', 'tokens', 'native', 'cryptocurrency', 'coin', 'coins'
    ]
    
    # Split the middle text into words
    words = middle_text.lower().split()
    
    # Find the boundary between number words and token words
    number_end_idx = 0
    for i, word in enumerate(words):
        if word in number_words or word.replace('.', '').isdigit():
            number_end_idx = i
        elif word in token_words and i > 0:
            # Found first token word, so the number part ends at the previous word
            break
    
    # Extract amount text and token text
    amount_text = ' '.join(words[:number_end_idx + 1])
    token_text = ' '.join(words[number_end_idx + 1:])
    
    # If we couldn't split properly, try another approach
    if not amount_text or not token_text:
        # Try to match a numeric amount first
        numeric_pattern = r'(\d+(?:\.\d+)?)'
        numeric_match = re.search(numeric_pattern, middle_text)
        if numeric_match:
            amount_text = numeric_match.group(1)
            # Remove the amount from the middle text to get the token
            token_text = middle_text.replace(amount_text, '', 1).strip()
        else:
            # Try different split points to find a valid number and token
            for i in range(1, len(words)):
                potential_amount = ' '.join(words[:i])
                potential_token = ' '.join(words[i:])
                
                # Check if potential_amount can be converted to a number
                amount_val = text_to_number(potential_amount)
                if amount_val is not None:
                    amount_text = potential_amount
                    token_text = potential_token
                    break
    
    # Convert amount text to number
    if amount_text:
        if amount_text.replace('.', '').isdigit():
            amount = float(amount_text)
        else:
            amount = text_to_number(amount_text)
            if amount is None:
                return None
    else:
        return None
    
    # Normalize token
    token = normalize_token_name(token_text)
    if not token:
        return None
    
    return {
        'action': action,
        'amount': amount,
        'token': token,
        'recipient': address
    }

def parse_nft_intent(user_input: str):
    """
    Parse natural language intent for creating NFTs
    """
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
