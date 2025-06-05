import os
import json
from openai import OpenAI
from typing import Optional, Dict

class AIIntentParser:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.perplexity.ai"
        )  # Fixed: Added missing closing parenthesis
        
        self.system_prompt = """Analyze Algorand-related requests and return JSON with:
{
  "intent": "send_algo|send_algo_multi|create_wallet|connect_wallet|create_nft|disconnect|balance|create_nft_with_image|create_nft|send_nft|send_nft_multi",
  "parameters": {
    "amount": float,
    "recipient": "address", 
    "recipients": [{"address": "string", "amount": float}],
    "total_amount": float,
    "name": "string",
    "supply": int,
    "description": "string",
    "image_url": "string"
    "asset_id": int
  }
}

IMPORTANT: For NFT creation, extract the actual name from various phrasings:

Examples:
User: "Hey, send 3 ALGO to K54ZTTHNDB..."
{"intent": "send_algo", "parameters": {"amount": 3, "recipient": "K54ZTTHNDB..."}}

User: "Send 5 ALGO to ADDRESS1 and 3 ALGO to ADDRESS2"
{"intent": "send_algo_multi", "parameters": {"recipients": [{"address": "ADDRESS1", "amount": 5}, {"address": "ADDRESS2", "amount": 3}], "total_amount": 8}}

User: "Send 10 ALGO to ADDRESS1, ADDRESS2, ADDRESS3"
{"intent": "send_algo_multi", "parameters": {"recipients": [{"address": "ADDRESS1", "amount": 3.33}, {"address": "ADDRESS2", "amount": 3.33}, {"address": "ADDRESS3", "amount": 3.34}], "total_amount": 10}}

User: "Send 2 ALGO each to ADDRESS1 and ADDRESS2"
{"intent": "send_algo_multi", "parameters": {"recipients": [{"address": "ADDRESS1", "amount": 2}, {"address": "ADDRESS2", "amount": 2}], "total_amount": 4}}

User: "Create a new wallet"
{"intent": "create_wallet", "parameters": {}}

User: "Check my balance"
{"intent": "balance", "parameters": {}}

User: "Create NFT named Dragon"
{"intent": "create_nft", "parameters": {"name": "Dragon"}}

User: "create an nft with this image named 'based'"
{"intent": "create_nft", "parameters": {"name": "based"}}

User: "Create an NFT called PixelArt with supply 100"
{"intent": "create_nft", "parameters": {"name": "PixelArt", "supply": 100}}

User: "Make NFT with name 'Demon Slayer' and supply 2"
{"intent": "create_nft", "parameters": {"name": "Demon Slayer", "supply": 2}}

User: "create an nft with this image named \"CoolArt\""
{"intent": "create_nft", "parameters": {"name": "CoolArt"}}

User: "create 10 nfts name cool style"
{"intent": "create_nft", "parameters": {"name": "cool style", "supply": 10}}

User: "create nft name cool style, 10 only"
{"intent": "create_nft", "parameters": {"name": "cool style", "supply": 10}}

User: "Opt-in to NFT 123456"
{"intent": "opt_in", "parameters": {"asset_id": 123456}}

User: "Opt out of asset 654321"
{"intent": "opt_out", "parameters": {"asset_id": 654321}}

User: "Opt-in to NFT 123456"
{"intent": "opt_in", "parameters": {"asset_id": 123456}}

User: "opt in for asset id 740574628"
{"intent": "opt_in", "parameters": {"asset_id": 740574628}}

User: "opt in for the asset 740574628"
{"intent": "opt_in", "parameters": {"asset_id": 740574628}}

User: "Opt out of asset 654321"
{"intent": "opt_out", "parameters": {"asset_id": 654321}}

User: "opt out for asset id 740574628"
{"intent": "opt_out", "parameters": {"asset_id": 740574628}}

User: "opt out for the asset 740574628"
{"intent": "opt_out", "parameters": {"asset_id": 740574628}}

User: "Send NFT 123 to ADDRESS"
{"intent": "send_nft", "parameters": {"asset_id": 123, "recipient": "ADDRESS"}}

User: "Send NFT 123 to ADDRESS"
{"intent": "send_nft", "parameters": {"asset_id": 123, "recipient": "ADDRESS"}}

User: "Transfer NFT 456 to ADDRESS1 and ADDRESS2"
{"intent": "send_nft_multi", "parameters": {"asset_id": 456, "recipients": ["ADDRESS1", "ADDRESS2"]}}"""

    def parse(self, user_input: str) -> Optional[Dict]:
        try:
            response = self.client.chat.completions.create(
                model="sonar-pro",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                max_tokens=200
            )  # Fixed: Added missing closing parenthesis
            return self._extract_json(response.choices[0].message.content)
        except Exception as e:
            print(f"AI Parsing Error: {e}")
            return None

    def _extract_json(self, text: str) -> Dict:
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            return json.loads(text[start:end])
        except:
            return {"intent": "unknown"}
