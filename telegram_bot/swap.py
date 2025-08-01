import requests
import json

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
