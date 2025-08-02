import requests
import json
from algosdk import encoding
from wallet import sign_transaction
import base64
from algosdk.transaction import Transaction, SignedTransaction
from algosdk.transaction import (
    Transaction, SignedTransaction, MultisigTransaction, LogicSigTransaction,
    calculate_group_id, assign_group_id
)
from typing import List, Union, Optional


def get_swap_quote(to_asa):
    url = f"https://api.vestigelabs.org/swap/v4?from_asa=0&to_asa={to_asa}&amount=1&mode=sef&denominating_asset_id={to_asa}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_swap_transactions(quote, address):
    url = f"https://api.vestigelabs.org/swap/v4/transactions?sender={address}&slippage=0.005"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(quote))
    response.raise_for_status()
    return response.json()

def search_asset(query):
    url = f"https://api.vestigelabs.org/assets/search?query={query}&network_id=0&denominating_asset_id=0&limit=50&offset=0&order_dir=desc"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if not data.get("results"):
        return None

    for asset in data["results"]:
        labels = asset.get("labels", [])
        if 2 in labels and 6 in labels:
            return asset.get("id")
    
    return None


import base64
from typing import List, Optional
from algosdk.encoding import msgpack
from algosdk.transaction import (
    Transaction, SignedTransaction, calculate_group_id, assign_group_id
)

def execute_swap_transactions(
    txns: List[dict],
    algod_client,
    password: Optional[str] = None,
    frontend='cli'
):
    """
    Decode the Vestige-supplied txn dicts, ask your wallet to sign each,
    normalize the result to a valid SignedTransaction (or multisig / logic-sig),
    send the atomic group, wait for confirmation, and return the pending info.
    """
    # 1) Decode raw txns to Transaction objects
    unsigned_list: List[Transaction] = []
    for raw in txns:
        txn_bytes = base64.b64decode(raw["txn"])
        d = msgpack.unpackb(txn_bytes)
        t = Transaction.undictify(d)
        unsigned_list.append(t)

    # 2) Assign group id for atomic cross-check
    calculate_group_id(unsigned_list)
    assign_group_id(unsigned_list)

    signed_list: List[Union[SignedTransaction, MultisigTransaction, LogicSigTransaction]] = []

    for idx, txn in enumerate(unsigned_list):
        result = sign_transaction(txn, password, "telegram")
        print(result)
        print(f"[DEBUG] Wallet returned type: {type(result)}")

        normalized = None

        if isinstance(result, dict):
            print(f"[DEBUG] Wallet returned a dict with keys: {list(result.keys())[:5]} ...")
            # Try to reconstruct a SignedTransaction (or multisig / logic-sig)
            if result.get("txn") is not None and result.get("sig") is not None and "msig" not in result:
                normalized = SignedTransaction.undictify(result)
            elif result.get("msig") is not None:
                normalized = MultisigTransaction.undictify(result)
            elif result.get("lsig") is not None:
                normalized = LogicSigTransaction.undictify(result)
            else:
                raise TypeError(f"Unknown signature format: missing sig/msig/lsig in dict: {result.keys()}")

        elif isinstance(result, SignedTransaction):
            normalized = result

        elif isinstance(result, MultisigTransaction):
            normalized = result

        elif isinstance(result, LogicSigTransaction):
            normalized = result

        else:
            raise TypeError(f"Unsupported return type from wallet: {type(result)}")

        # Sanity check
        if not isinstance(normalized, (SignedTransaction, MultisigTransaction, LogicSigTransaction)):
            raise TypeError(f"After normalization, unexpected type: {type(normalized)} at index {idx}")

        signed_list.append(normalized)

    # All txns now validated: send to Algod
    txid = algod_client.send_transactions(signed_list)
    print("✅ Submitted:", signed_list[0].get_txid() if isinstance(signed_list[0], SignedTransaction) else "group-first")
    confirmed_info = wait_for_confirmation(algod_client, txid)
    return confirmed_info
def wait_for_confirmation(client, txid, timeout=4):
    last_round = client.status().get('last-round')
    for _ in range(timeout):
        pending = client.pending_transaction_info(txid)
        if pending.get('confirmed-round', 0) > 0:
            return pending
        last_round += 1
        client.status_after_block(last_round)
    raise Exception("❌ Transaction not confirmed in time")




if __name__ == "__main__":
    try:
        print("Searching for asset 'GONNA'...")
        asset_id = search_asset("GONNA")
        if asset_id:
            print(f"Found asset with ID: {asset_id}")
            print("Getting swap quote...")
            quote = get_swap_quote(asset_id)
            print("Getting swap transactions...")
            transactions = get_swap_transactions(quote, "LEGENDMQQJJWSQVHRFK36EP7GTM3MTI3VD3GN25YMKJ6MEBR35J4SBNVD4")
            print(json.dumps(transactions, indent=2))
        else:
            print("No matching asset found for 'GONNA'")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
