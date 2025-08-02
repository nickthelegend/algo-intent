import requests
import json
from algosdk import encoding
from wallet import sign_transaction
import base64
from algosdk.transaction import Transaction, SignedTransaction

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


def execute_swap_transactions(txs: list, algod_client, password=None, frontend='cli'):
    signed_group = []

    for tx in txs:
        raw_txn_b64 = tx["txn"]
        txn_bytes = base64.b64decode(raw_txn_b64)
        txn_dict = encoding.msgpack.unpackb(txn_bytes)
        txn = Transaction.undictify(txn_dict)

        # Your custom wallet manager handles the signing
        signed = sign_transaction(txn, password=password, frontend=frontend)
        signed_group.append(signed)

    # Send the signed group
    txid = algod_client.send_transactions(signed_group)
    print(f"✅ Sent group transaction, txID: {txid}")
    confirmed = wait_for_confirmation(algod_client, txid)
    return confirmed
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
