"""
Wallet Module
Handles Algorand wallet connections and transactions using py-algorand-sdk
"""
import os
import base64
import json
import logging
from typing import Dict, Any, Tuple, Optional
import requests

from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import PaymentTxn, AssetTransferTxn
from utils import validate_algorand_address

from config import get_settings

logger = logging.getLogger(__name__)

class Account:
    """
    Simple class to store account information
    """
    def __init__(self, private_key, address):
        self.private_key = private_key
        self.address = address


def initialize_account() -> Account:
    """
    Initialize an account using the private key from environment variables
    
    Returns:
        Account: Account object with private key and address
    """
    settings = get_settings()
    
    # Get private key from settings (should be a mnemonic)
    private_key_mnemonic = settings.algod_private_key
    
    if not private_key_mnemonic:
        raise ValueError("Private key not found in environment variables")
    
    # Convert mnemonic to private key
    try:
        private_key = mnemonic.to_private_key(private_key_mnemonic)
        address = account.address_from_private_key(private_key)
        
        # Create account object
        return Account(private_key, address)
    except Exception as e:
        logger.error(f"Error initializing account: {e}")
        raise ValueError(f"Invalid private key mnemonic: {e}")

# def get_algod_client():
#     """
#     Create an Algorand client for interacting with the network
    
#     Returns:
#         AlgodClient: The Algorand client
#     """
#     settings = get_settings()
    
#     # Initialize connection to Algorand node
#     algod_address = settings.algod_address
#     algod_port = settings.algod_port
#     algod_token = settings.algod_token
    
#     # Create proper URL with port
#     if algod_address.startswith('http'):
#         # If it's a full URL, ensure port is properly formatted
#         if ':' in algod_address.split('//')[1]:
#             # URL already contains port, use as is
#             algod_url = algod_address
#         else:
#             # Add port to URL
#             algod_url = f"{algod_address}:{algod_port}"
#     else:
#         # If just a hostname, construct URL with protocol and port
#         algod_url = f"https://{algod_address}:{algod_port}"
    
#     headers = {
#         "X-API-Key": algod_token
#     }
    
#     # Create algod client
#     algod_client = algod.AlgodClient(algod_token, algod_url, headers)
#     return algod_client

# Get Algorand client parameters from environment variables
algod_token = os.getenv("TESTNET_ALGOD_TOKEN")
algod_url = os.getenv("TESTNET_ALGOD_URL")
algod_port = os.getenv("TESTNET_ALGOD_PORT")

# Initialize Algorand client
algod_client = algod.AlgodClient(algod_token, algod_url)

# Get suggested transaction parameters
suggested_params = algod_client.suggested_params()

def get_asset_id(token_name: str) -> int:
    """
    Get the asset ID for a token name
    
    Args:
        token_name (str): The name of the token (e.g., "ALGO", "USDC")
        
    Returns:
        int: The asset ID (0 for ALGO)
    """
    settings = get_settings()
    
    # ALGO is the native token, represented by asset ID 0
    if token_name.upper() == "ALGO":
        return 0
        
    # Look up other assets - in a real application, this would be more comprehensive
    # You might fetch this from an API or database
    asset_map = {
        "USDC": settings.usdc_asset_id,
        # Add more assets as needed
    }
    
    asset_id = asset_map.get(token_name.upper())
    if asset_id is None:
        raise ValueError(f"Unknown token: {token_name}")
        
    return int(asset_id)

def create_transaction(sender_address: str, intent: Dict[str, Any]) -> Any:
    algod_client = get_algod_client()
    params = algod_client.suggested_params()

    action = intent.get("action")
    amount = intent.get("amount")
    token = intent.get("token", "ALGO").upper()
    receiver = intent.get("receiver")

    # Validate required fields
    if not action or amount is None or not receiver:
        raise ValueError("Missing required fields in intent")
    if not validate_algorand_address(receiver):
        raise ValueError(f"Invalid Algorand address: {receiver}")

    # Determine asset_id (0 for ALGO, otherwise look up ASA)
    asset_id = 0
    if token != "ALGO":
        # You may want to map token names to asset IDs here
        # For example: asset_id = lookup_asset_id(token)
        # For now, raise an error if not ALGO
        raise ValueError(f"Only ALGO transactions are supported in this version. Asset: {token}")

    # ALGO Payment Transaction
    if asset_id == 0:
        try:
            # Convert ALGO to microAlgos
            amount_microalgo = int(float(amount) * 1_000_000)
        except Exception as e:
            raise ValueError(f"Invalid amount: {amount}. Error: {e}")

        unsigned_txn = PaymentTxn(
            sender=sender_address,
            sp=params,
            receiver=receiver,
            amt=amount_microalgo,
            note=f"Intent: {action} {amount} {token}".encode()
        )

# payment_txn = transaction.PaymentTxn(
#     sender=address,
#     sp=suggested_params,
#     amt=util.algos_to_microalgos(0.5),
#     receiver="XBQF2K6VM5DP523MML4EGNCIJUQSILI5MGJNV3JITOZOZHWPNGJEORYJ6U"
# )
        return unsigned_txn

    # (Optional) Add ASA transaction support here
    # else:
    #     amount_base_units = int(float(amount) * 1_000_000)  # Adjust decimals as needed
    #     unsigned_txn = AssetTransferTxn(
    #         sender=sender_address,
    #         sp=params,
    #         receiver=receiver,
    #         amt=amount_base_units,
    #         index=asset_id,
    #         note=f"Intent: {action} {amount} {token}".encode()
    #     )
    #     return unsigned_txn

def sign_transaction(unsigned_txn) -> str:
    try:
        signed_txn = unsigned_txn.sign(PRIVATE_KEY)
        return signed_txn
    except Exception as e:
        logger.error(f"Error signing transaction: {e}")
        raise

def submit_transaction(signed_txn) -> str:
    algod_client = get_algod_client()
    try:
        txid = algod_client.send_transaction(signed_txn)
        return txid
    except Exception as e:
        logger.error(f"Error submitting transaction: {e}")
        raise

def wait_for_confirmation(algod_client, tx_id: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Wait for transaction confirmation
    
    Args:
        algod_client: The Algorand client
        tx_id (str): The transaction ID
        timeout (int): Maximum number of rounds to wait
        
    Returns:
        Dict[str, Any]: Transaction confirmation details
    """
    start_round = algod_client.status()["last-round"] + 1
    current_round = start_round
    
    while current_round < start_round + timeout:
        try:
            pending_txn = algod_client.pending_transaction_info(tx_id)
            if pending_txn.get("confirmed-round", 0) > 0:
                return pending_txn
        except Exception as e:
            logger.error(f"Error checking transaction: {e}")
            
        # Wait for the next round
        algod_client.status_after_block(current_round)
        current_round += 1
        
    raise TimeoutError(f"Transaction {tx_id} not confirmed after {timeout} rounds")