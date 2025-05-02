from algosdk.transaction import PaymentTxn
from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
from algosdk import mnemonic
from utils import validate_address, check_account_balance

class TransactionError(Exception):
    pass

class NFTCreationError(Exception):
    pass

def build_and_send_transaction(sender, recipient, amount, algod_client, sender_mnemonic, dry_run=False):
    if not validate_address(recipient):
        raise TransactionError("❌ Invalid recipient address format.")
    if not sender or not sender_mnemonic:
        raise TransactionError("❌ Sender address or mnemonic not configured.")
    try:
        has_sufficient_funds, balance = check_account_balance(sender, amount, algod_client)
        if not has_sufficient_funds:
            raise TransactionError(f"❌ Insufficient balance to complete transaction. Available: {balance:.6f} ALGO, Required: {amount:.6f} ALGO")
        params = algod_client.suggested_params()
        amount_microalgos = int(amount * 1_000_000)
        unsigned_txn = PaymentTxn(sender, params, recipient, amount_microalgos)
        if dry_run:
            return {
                'status': 'dry_run',
                'transaction': unsigned_txn,
                'message': f"✅ Dry run successful. Would send {amount:.6f} ALGO to {recipient}"
            }
        private_key = mnemonic.to_private_key(sender_mnemonic)
        signed_txn = unsigned_txn.sign(private_key)
        txid = algod_client.send_transaction(signed_txn)
        return {
            'status': 'success',
            'txid': txid,
            'message': f"✅ Transaction sent! {amount:.6f} ALGO sent to {recipient}. TxID: {txid}"
        }
    except Exception as e:
        if isinstance(e, TransactionError):
            raise e
        raise TransactionError(f"❌ Transaction failed: {str(e)}")

def create_nft(name, unit_name, total_supply, description, algod_client, sender, sender_mnemonic):
    if not name:
        raise NFTCreationError("❌ NFT name is required.")
    if not sender or not sender_mnemonic:
        raise NFTCreationError("❌ Creator address or mnemonic missing.")
    try:
        params = algod_client.suggested_params()
        total_supply = int(total_supply)
        txn = AssetConfigTxn(
            sender=sender,
            sp=params,
            total=total_supply,
            default_frozen=False,
            unit_name=unit_name,
            asset_name=name,
            manager=sender,
            reserve=sender,
            freeze=sender,
            clawback=sender,
            url="",
            decimals=0,
            note=description.encode() if description else None
        )
        private_key = mnemonic.to_private_key(sender_mnemonic)
        signed_txn = txn.sign(private_key)
        txid = algod_client.send_transaction(signed_txn)
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
        asset_id = confirmed_txn["asset-index"]
        return asset_id
    except Exception as e:
        raise NFTCreationError(f"❌ NFT creation failed: {e}")
