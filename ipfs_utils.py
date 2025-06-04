import os
import requests

PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_API_SECRET = os.getenv("PINATA_API_SECRET")
PINATA_ENDPOINT = "https://api.pinata.cloud/pinning/pinFileToIPFS"

def upload_to_ipfs(file_path):
    """
    Upload files (images/videos) to IPFS using Pinata.
    Supports files up to 1GB with extended timeout for videos.
    """
    if not PINATA_API_KEY or not PINATA_API_SECRET:
        raise EnvironmentError("Missing Pinata credentials.")

    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_API_SECRET
    }

    try:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        
        # Validate file size (1GB = 1024MB)
        if file_size > 1024:
            raise ValueError(f"File too large ({file_size:.2f}MB). Max size: 1GB")

        print(f"Uploading {file_name} ({file_size:.2f}MB) to IPFS...")

        with open(file_path, "rb") as fp:
            files = {"file": (file_name, fp)}
            
            # Extended timeout for larger files (10 minutes)
            timeout = 600 if file_size > 50 else 120
            
            response = requests.post(
                PINATA_ENDPOINT,
                headers=headers,
                files=files,
                timeout=timeout
            )
            
        if response.status_code != 200:
            raise Exception(f"Pinata upload failed: HTTP {response.status_code} - {response.text}")
            
        result = response.json()
        if "IpfsHash" not in result:
            raise Exception("Pinata response missing IPFS hash")
            
        print(f"Successfully uploaded to IPFS: {result['IpfsHash']}")
        return f"ipfs://{result['IpfsHash']}"

    except requests.exceptions.Timeout:
        raise Exception(f"Upload timed out after {timeout/60:.1f} minutes")
    except Exception as e:
        raise Exception(f"Failed to upload {file_name}: {str(e)}")
