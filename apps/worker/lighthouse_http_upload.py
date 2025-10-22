"""
Direct Lighthouse HTTP API Upload (bypassing SDK)

This is a fallback implementation that uses Lighthouse's HTTP API directly
instead of the Node.js SDK, which is failing with internal errors.
"""

import requests
import json
from pathlib import Path
from eth_account import Account
from eth_account.messages import encode_defunct


class LighthouseHTTPUpload:
    """Direct HTTP API implementation for Lighthouse uploads"""
    
    def __init__(self, api_key: str, private_key: str):
        self.api_key = api_key
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.wallet_address = self.account.address
        self.base_url = "https://node.lighthouse.storage"
        
    def get_auth_message(self):
        """Get authentication message from Lighthouse"""
        url = f"{self.base_url}/api/auth/get_message"
        params = {"publicKey": self.wallet_address}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        message_text = data.get("message") if isinstance(data, dict) else data
        
        return message_text
    
    def sign_message(self, message_text: str):
        """Sign message with private key"""
        message_hash = encode_defunct(text=message_text)
        signed = self.account.sign_message(message_hash)
        signature_hex = signed.signature.hex()
        
        if not signature_hex.startswith("0x"):
            signature_hex = "0x" + signature_hex
            
        return signature_hex
    
    def upload_encrypted(self, file_path: str):
        """Upload encrypted file directly via HTTP API"""
        # Get and sign auth message
        message_text = self.get_auth_message()
        signature = self.sign_message(message_text)
        
        # Prepare file for upload
        abs_file_path = str(Path(file_path).resolve())
        
        # Upload endpoint
        url = f"{self.base_url}/api/v0/add"
        
        # Prepare multipart form data
        with open(abs_file_path, 'rb') as f:
            files = {
                'file': (Path(abs_file_path).name, f, 'application/octet-stream')
            }
            
            # Headers with authentication
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'publicKey': self.wallet_address,
                'signature': signature
            }
            
            # Make request
            response = requests.post(
                url,
                files=files,
                headers=headers,
                timeout=180
            )
            
            response.raise_for_status()
            result = response.json()
            
        return {
            "cid": result["Hash"],
            "name": result["Name"],
            "size": result["Size"]
        }
    
    def apply_access_control(self, cid: str, conditions: dict):
        """Apply access control conditions to uploaded file"""
        url = f"{self.base_url}/api/accessControl/apply"
        
        # Get and sign auth message
        message_text = self.get_auth_message()
        signature = self.sign_message(message_text)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "cid": cid,
            "publicKey": self.wallet_address,
            "signedMessage": signature,
            "conditions": conditions
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        return response.json()
