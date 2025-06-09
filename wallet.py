import os
import json
from algosdk import account, mnemonic
import base64
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

WALLET_FILE = "wallet.json"
SESSION_FILE = ".wallet_session"

class WalletManager:
    def __init__(self):
        self.connected_address = None
        self._load_session()
    
    def _load_session(self):
        """Load active wallet session if it exists"""
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r') as f:
                    session = json.load(f)
                    self.connected_address = session.get('address')
            except:
                self.connected_address = None
    
    def _save_session(self):
        """Save current wallet session"""
        with open(SESSION_FILE, 'w') as f:
            json.dump({'address': self.connected_address}, f)
    
    def create_wallet(self, password=None):
        """Create a new Algorand wallet and store it securely"""
        # Generate new account
        private_key, address = account.generate_account()
        passphrase = mnemonic.from_private_key(private_key)
        
        # Get password for encrypting the wallet
        if not password:
            password = getpass.getpass("Create a password to secure your wallet: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                raise ValueError("Passwords do not match")
        
        # Encrypt the wallet data
        encrypted_mnemonic = self._encrypt_data(passphrase, password)
        wallet_data = {
            "address": address,
            "encrypted_mnemonic": encrypted_mnemonic
        }
        
        # Save wallet data
        self._save_wallet(wallet_data)
        
        # Set as active wallet
        self.connected_address = address
        self._save_session()
        
        # Return display data (no sensitive info)
        return {
            "address": address,
            "mnemonic": passphrase,  # Return mnemonic ONLY during creation for backup
            "encrypted_mnemonic": encrypted_mnemonic,  # Added for Telegram bot
            "message": "⚠️ IMPORTANT: Save this mnemonic phrase securely. It will not be shown again!"
        }
    
    def connect_wallet(self, passphrase=None, password=None):
        """Connect to a wallet using its mnemonic passphrase"""
        if not passphrase:
            passphrase = getpass.getpass("Enter your 25-word mnemonic phrase: ")
        
        try:
            # Validate mnemonic by deriving private key
            private_key = mnemonic.to_private_key(passphrase)
            address = account.address_from_private_key(private_key)
            
            # Get password for encrypting the wallet
            if not password:
                password = getpass.getpass("Create a password to secure this wallet: ")
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    raise ValueError("Passwords do not match")
            
            # Encrypt the wallet data
            encrypted_mnemonic = self._encrypt_data(passphrase, password)
            wallet_data = {
                "address": address,
                "encrypted_mnemonic": encrypted_mnemonic
            }
            
            # Save wallet data
            self._save_wallet(wallet_data)
            
            # Set as active wallet
            self.connected_address = address
            self._save_session()
            
            return {
                "address": address,
                "encrypted_mnemonic": encrypted_mnemonic,  # Added for Telegram bot
                "message": "Wallet connected successfully"
            }
        except Exception as e:
            raise ValueError(f"Invalid mnemonic: {e}")
    
    def disconnect_wallet(self):
        """Disconnect the current wallet"""
        self.connected_address = None
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        return {"message": "Wallet disconnected"}
    
    def get_connected_wallet(self):
        """Get the currently connected wallet address"""
        if not self.connected_address:
            return None
        return {"address": self.connected_address}
    
    def get_transaction_details(self, txn):
        """Get transaction details for display"""
        details = {
            "from": getattr(txn, 'sender', None),
            "to": getattr(txn, 'receiver', None),
            "amount_microalgos": getattr(txn, 'amt', None),
            "fee_microalgos": getattr(txn, 'fee', None),
            "type": type(txn).__name__
        }
        
        if hasattr(txn, 'asset_name'):
            details["asset_name"] = txn.asset_name
        if hasattr(txn, 'total'):
            details["total_supply"] = txn.total
            
        return details
        
    def sign_transaction(self, txn, password=None, frontend='cli'):
        """Handle transaction signing for different frontends"""
        if not self.connected_address:
            raise ValueError("No wallet connected")
        
        wallet_data = self._load_wallet_by_address(self.connected_address)
        if not wallet_data:
            raise ValueError("Wallet data not found")
        
        # Load wallet data
        wallet_data = self._load_wallet_by_address(self.connected_address)
        if not wallet_data:
            raise ValueError("Wallet data not found")
            
        # For Telegram: Return details instead of CLI prompts
        if frontend == 'telegram' and not password:
            return {
                "needs_approval": True,
                "txn_details": {
                    "from": txn.sender,
                    "to": getattr(txn, 'receiver', 'N/A'),
                    "amount": getattr(txn, 'amt', 0) / 1_000_000,
                    "type": type(txn).__name__
                },
                "unsigned_txn": txn
            }
        
        # For CLI: show details and ask for approval
        if frontend == 'cli':
            print("\n📝 Transaction Details:")
            if hasattr(txn, 'sender'):
                print(f"From: {txn.sender}")
            if hasattr(txn, 'receiver'):
                print(f"To: {txn.receiver}")
                print(f"Amount: {txn.amt / 1_000_000} ALGO")
            elif hasattr(txn, 'asset_name'):
                print(f"Asset Name: {txn.asset_name}")
            print(f"Fee: {txn.fee / 1_000_000} ALGO")
            
            # Request password to decrypt mnemonic
            password = getpass.getpass("\nEnter your wallet password to sign this transaction: ")
            
            # Request explicit approval
            approval = input("\n⚠️ Do you approve this transaction? (y/n): ")
            if approval.lower() != 'y':
                raise ValueError("Transaction rejected by user")
        
        # Sign the transaction
        try:
            # Decrypt mnemonic
            decrypted_mnemonic = self._decrypt_data(wallet_data["encrypted_mnemonic"], password)
            
            # Get private key
            private_key = mnemonic.to_private_key(decrypted_mnemonic)
            
            # Sign transaction
            signed_txn = txn.sign(private_key)
            return signed_txn
        except Exception as e:
            raise ValueError(f"Failed to sign transaction: {e}")
    
    def _encrypt_data(self, data, password):
        """Encrypt sensitive data with a password"""
        password_bytes = password.encode()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return base64.b64encode(salt + encrypted_data).decode()
    
    def _decrypt_data(self, encrypted_data, password):
        """Decrypt sensitive data with a password"""
        try:
            password_bytes = password.encode()
            decoded = base64.b64decode(encrypted_data)
            salt, encrypted_data = decoded[:16], decoded[16:]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError("Incorrect password or corrupted data")
    
    def _save_wallet(self, wallet_data):
        """Save wallet data to file"""
        # Create wallets directory if it doesn't exist
        os.makedirs("wallets", exist_ok=True)
        
        # Save wallet data to a file named by its address
        wallet_file = f"wallets/{wallet_data['address']}.json"
        with open(wallet_file, 'w') as f:
            json.dump(wallet_data, f)
        
        # Update wallet index
        self._update_wallet_index(wallet_data['address'])
    
    def _update_wallet_index(self, address):
        """Update the wallet index with the new address"""
        wallets = []
        if os.path.exists(WALLET_FILE):
            try:
                with open(WALLET_FILE, 'r') as f:
                    wallets = json.load(f)
            except:
                wallets = []
        
        # Make sure wallets is a list, not a dict
        if isinstance(wallets, dict):
            wallets = list(wallets.values())
        
        # Add address if not already in the list
        if address not in wallets:
            wallets.append(address)
        
        with open(WALLET_FILE, 'w') as f:
            json.dump(wallets, f)
    
    def _load_wallet_by_address(self, address):
        """Load wallet data for a specific address"""
        wallet_file = f"wallets/{address}.json"
        if not os.path.exists(wallet_file):
            return None
        
        try:
            with open(wallet_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def list_wallets(self):
        """List all saved wallets"""
        if not os.path.exists(WALLET_FILE):
            return []
        
        try:
            with open(WALLET_FILE, 'r') as f:
                addresses = json.load(f)
                # Make sure addresses is a list
                if isinstance(addresses, dict):
                    addresses = list(addresses.values())
                return [{"address": addr, "active": addr == self.connected_address} for addr in addresses]
        except:
            return []

# Create a global wallet manager instance
wallet_manager = WalletManager()

# Convenience functions that use the wallet manager
def create_wallet(password=None):
    return wallet_manager.create_wallet(password)

def connect_wallet(mnemonic=None, password=None):
    return wallet_manager.connect_wallet(mnemonic, password)

def disconnect_wallet():
    return wallet_manager.disconnect_wallet()

def get_connected_wallet():
    return wallet_manager.get_connected_wallet()

def list_wallets():
    return wallet_manager.list_wallets()

def sign_transaction(txn, password=None, frontend='cli'):
    return wallet_manager.sign_transaction(txn, password, frontend)

def format_wallet_display(wallet_data):
    """Format wallet data for display (hiding private key)"""
    address = wallet_data["address"]
    # If mnemonic is included (only during wallet creation)
    if "mnemonic" in wallet_data:
        mnemonic_words = wallet_data["mnemonic"].split()
        if len(mnemonic_words) >= 6:
            formatted_mnemonic = " ".join(mnemonic_words[:3]) + " ... " + " ".join(mnemonic_words[-3:])
        else:
            formatted_mnemonic = wallet_data["mnemonic"]
        return {
            "address": address,
            "mnemonic_preview": formatted_mnemonic,
            "address_short": f"{address[:8]}...{address[-8:]}"
        }
    else:
        return {
            "address": address,
            "address_short": f"{address[:8]}...{address[-8:]}"
        }
