import os
import requests

PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_API_SECRET = os.getenv("PINATA_API_SECRET")
PINATA_ENDPOINT = "https://api.pinata.cloud/pinning/pinFileToIPFS"

def upload_to_ipfs(file_path):
    """
    Upload a file to IPFS using Pinata.
    Returns: ipfs://... URL on success, raises Exception on error.
    """
    if not PINATA_API_KEY or not PINATA_API_SECRET:
        raise EnvironmentError("Missing Pinata credentials. Set PINATA_API_KEY and PINATA_API_SECRET in your environment.")

    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_API_SECRET
    }

    try:
        with open(file_path, "rb") as fp:
            files = {"file": (os.path.basename(file_path), fp)}
            response = requests.post(PINATA_ENDPOINT, headers=headers, files=files, timeout=60)
        if response.status_code != 200:
            raise Exception(f"Pinata upload failed: HTTP {response.status_code} - {response.text}")
        result = response.json()
        if "IpfsHash" not in result:
            raise Exception(f"Pinata upload failed: Unexpected response: {result}")
        return f"ipfs://{result['IpfsHash']}"
    except Exception as e:
        raise Exception(f"Pinata IPFS upload failed: {e}")
