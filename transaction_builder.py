from algosdk.transaction import PaymentTxn, AssetConfigTxn, AssetTransferTxn, wait_for_confirmation, assign_group_id
from utils import validate_address, check_account_balance
from wallet import sign_transaction

class TransactionError(Exception):
    pass

class NFTCreationError(Exception):
    pass

def build_and_send_transaction(sender, recipient, amount, algod_client, password=None, frontend='cli', dry_run=False):
    """
    Build and send a transaction using the connected wallet
    frontend: 'cli' or 'telegram'
    """
    if not validate_address(recipient):
        raise TransactionError("❌ Invalid recipient address format.")
    if not sender:
        raise TransactionError("❌ Sender address not provided.")

    try:
        has_sufficient_funds, balance = check_account_balance(sender, amount, algod_client)
        if not has_sufficient_funds:
            raise TransactionError(f"❌ Insufficient balance. Available: {balance:.6f} ALGO, Required: {amount:.6f} ALGO")

        # Get suggested parameters
        params = algod_client.suggested_params()
        
        # Convert ALGO to microALGO
        amount_microalgos = int(amount * 1_000_000)
        
        # Build unsigned transaction
        unsigned_txn = PaymentTxn(sender, params, recipient, amount_microalgos)
        
        if dry_run:
            return {
                'status': 'dry_run',
                'transaction': unsigned_txn,
                'message': f"✅ Dry run successful. Would send {amount:.6f} ALGO to {recipient}"
            }
        
        # Sign transaction with appropriate frontend
        sign_result = sign_transaction(unsigned_txn, password=password, frontend=frontend)
        
        # If we need approval (Telegram case), return details for user confirmation
        if isinstance(sign_result, dict) and sign_result.get("needs_approval"):
            return {
                'status': 'awaiting_approval',
                'txn_details': sign_result['txn_details'],
                'unsigned_txn': sign_result['unsigned_txn']
            }
        
        # Send transaction
        txid = algod_client.send_transaction(sign_result)
        
        return {
            'status': 'success',
            'txid': txid,
            'message': f"✅ Transaction sent! {amount:.6f} ALGO sent to {recipient}. TxID: {txid}"
        }
        
    except Exception as e:
        if isinstance(e, TransactionError):
            raise e
        raise TransactionError(f"❌ Transaction failed: {str(e)}")
    
def build_and_send_multi_transaction(sender, recipients, algod_client, password=None, frontend='cli'):
    """
    Build and send atomic transfer to multiple recipients
    recipients: [{"address": "...", "amount": 5.0}, ...]
    """
    if not recipients or len(recipients) < 2:
        raise TransactionError("❌ Multi-recipient transfer requires at least 2 recipients.")
    
    # Validate all recipients
    for i, recipient in enumerate(recipients):
        if not validate_address(recipient['address']):
            raise TransactionError(f"❌ Invalid recipient address #{i+1}")
        if recipient['amount'] <= 0:
            raise TransactionError(f"❌ Invalid amount for recipient #{i+1}")
    
    # Calculate total amount
    total_amount = sum(r['amount'] for r in recipients)
    
    # Check balance
    has_sufficient_funds, balance = check_account_balance(sender, total_amount, algod_client)
    if not has_sufficient_funds:
        raise TransactionError(f"❌ Insufficient balance. Available: {balance:.6f} ALGO, Required: {total_amount:.6f} ALGO")
    
    try:
        # Get suggested parameters
        params = algod_client.suggested_params()
        
        # Create unsigned transactions for each recipient
        unsigned_txns = []
        for recipient in recipients:
            amount_microalgos = int(recipient['amount'] * 1_000_000)
            txn = PaymentTxn(
                sender=sender,
                sp=params,
                receiver=recipient['address'],
                amt=amount_microalgos
            )
            unsigned_txns.append(txn)
        
        # Group the transactions (this makes them atomic)
        grouped_txns = assign_group_id(unsigned_txns)
        
        if frontend == 'telegram':
            return {
                'status': 'awaiting_approval',
                'unsigned_txns': grouped_txns,
                'recipients': recipients,
                'total_amount': total_amount
            }
        
        # For CLI: sign all transactions
        signed_txns = []
        for txn in grouped_txns:
            signed_txn = sign_transaction(txn, password=password, frontend=frontend)
            signed_txns.append(signed_txn)
        
        # Send the group
        txid = algod_client.send_transactions(signed_txns)
        
        return {
            'status': 'success',
            'txid': txid,
            'message': f"✅ Multi-recipient transfer successful! {len(recipients)} payments sent. TxID: {txid}",
            'recipients': recipients,
            'total_amount': total_amount
        }
        
    except Exception as e:
        raise TransactionError(f"❌ Multi-recipient transfer failed: {str(e)}")

def create_nft(name, unit_name, total_supply, description, algod_client, sender, password=None, frontend='cli', url=None):
    """
    Create an NFT using the connected wallet
    """
    if not name:
        raise NFTCreationError("❌ NFT name is required.")
    if not sender:
        raise NFTCreationError("❌ Creator address missing.")

    try:
        params = algod_client.suggested_params()
        total_supply = int(total_supply)
        
        # Build unsigned transaction
        txn = AssetConfigTxn(
            sender=sender,
            sp=params,
            total=total_supply,
            default_frozen=False,
            unit_name=unit_name[:8],  # Max 8 characters
            asset_name=name[:32],     # Max 32 characters
            manager=sender,
            reserve=sender,
            freeze=sender,
            clawback=sender,
            url=url or "",
            decimals=0,
            note=description.encode() if description else None
        )
                
        if frontend == 'telegram':
            return {
                'status': 'awaiting_approval',
                'unsigned_txn': txn,
            }
        
        # For CLI: sign and send immediately
        signed_txn = sign_transaction(txn, password=password, frontend=frontend)
        txid = algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation and get asset ID
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
        asset_id = confirmed_txn["asset-index"]
        
        return {
            'status': 'success',
            'asset_id': asset_id,
            'txid': txid
        }
        
    except Exception as e:
        raise NFTCreationError(f"❌ NFT creation failed: {e}")
    
def send_nft(sender, asset_id, recipient, algod_client, password=None, frontend='cli'):
    """Transfer NFT to single recipient"""
    try:
        params = algod_client.suggested_params()
        txn = AssetTransferTxn(
            sender=sender,
            sp=params,
            receiver=recipient,
            amt=1,
            index=asset_id
        )
        
        if frontend == 'telegram':
            return {
                'status': 'awaiting_approval',
                'unsigned_txn': txn,
                'txn_details': {
                    'type': 'nft_transfer',
                    'asset_id': asset_id,
                    'recipient': recipient
                }
            }
            
        signed_txn = sign_transaction(txn, password=password, frontend=frontend)
        txid = algod_client.send_transaction(signed_txn)
        return {'status': 'success', 'txid': txid}
        
    except Exception as e:
        raise TransactionError(f"NFT transfer failed: {str(e)}")

def send_nft_multi(sender, asset_id, recipients, algod_client, password=None, frontend='cli'):
    """Atomic transfer to multiple recipients"""
    try:
        params = algod_client.suggested_params()
        txns = []
        
        for recipient in recipients:
            txns.append(
                AssetTransferTxn(
                    sender=sender,
                    sp=params,
                    receiver=recipient,
                    amt=1,
                    index=asset_id
                )
            )
            
        # Group transactions
        grouped = assign_group_id(txns)
        
        if frontend == 'telegram':
            return {
                'status': 'awaiting_approval',
                'unsigned_txns': grouped,
                'txn_details': {
                    'type': 'nft_multi_transfer',
                    'asset_id': asset_id,
                    'recipients': recipients
                }
            }
            
        signed_group = []
        for txn in grouped:
            signed = sign_transaction(txn, password=password, frontend=frontend)
            signed_group.append(signed)
            
        txid = algod_client.send_transactions(signed_group)
        return {'status': 'success', 'txid': txid}
        
    except Exception as e:
        raise TransactionError(f"Multi-NFT transfer failed: {str(e)}")
    
def get_asset_id_from_txid(algod_client, txid):
    """Get asset ID from transaction ID (for NFT creation)"""
    try:
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
        return confirmed_txn['asset-index']
    except Exception as e:
        raise Exception(f"Asset ID lookup failed: {str(e)}")
    
def opt_in_to_asset(sender, asset_id, algod_client, password=None, frontend='cli'):
    """
    Opt-in to an Algorand ASA/NFT.
    """
    params = algod_client.suggested_params()
    txn = AssetTransferTxn(
        sender=sender,
        sp=params,
        receiver=sender,
        amt=0,
        index=asset_id
    )
    sign_result = sign_transaction(txn, password=password, frontend=frontend)
    if isinstance(sign_result, dict) and sign_result.get("needs_approval"):
        return {
            'status': 'awaiting_approval',
            'unsigned_txn': sign_result['unsigned_txn'],
            'txn_details': sign_result['txn_details']
        }
    txid = algod_client.send_transaction(sign_result)
    return {'status': 'success', 'txid': txid}

def opt_out_of_asset(sender, asset_id, algod_client, password=None, frontend='cli'):
    """
    Opt-out of an Algorand ASA/NFT (must have zero balance).
    """
    params = algod_client.suggested_params()
    txn = AssetTransferTxn(
        sender=sender,
        sp=params,
        receiver=sender,
        amt=0,
        index=asset_id,
        close_assets_to=sender
    )
    sign_result = sign_transaction(txn, password=password, frontend=frontend)
    if isinstance(sign_result, dict) and sign_result.get("needs_approval"):
        return {
            'status': 'awaiting_approval',
            'unsigned_txn': sign_result['unsigned_txn'],
            'txn_details': sign_result['txn_details']
        }
    txid = algod_client.send_transaction(sign_result)
    return {'status': 'success', 'txid': txid}