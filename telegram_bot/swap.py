import requests
import json

def get_swap_quote():
    url = "https://api.vestigelabs.org/swap/v4?from_asa=0&to_asa=2582294183&amount=1&mode=sef&denominating_asset_id=2582294183"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_swap_transactions(quote):
    url = "https://api.vestigelabs.org/swap/v4/transactions?sender=LEGENDMQQJJWSQVHRFK36EP7GTM3MTI3VD3GN25YMKJ6MEBR35J4SBNVD4&slippage=0.005"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(quote))
    response.raise_for_status()
    return response.json()

def search_asset(query):
    url = f"https://api.vestigelabs.org/assets/search?query={query}&network_id=0&denominating_asset_id=0&limit=50&offset=0&order_dir=desc"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    try:
        quote = get_swap_quote()
        transactions = get_swap_transactions(quote)
        print(json.dumps(transactions, indent=2))
        print("\nSearching for asset 'GONNA':")
        assets = search_asset("GONNA")
        print(json.dumps(assets, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")