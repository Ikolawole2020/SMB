"""
Paystack Transfer Integration for Nigerian Bank Transfers
"""

import requests
from flask import current_app

def create_transfer_recipient(name, account_number, bank_code):
    """Create a transfer recipient for Nigerian bank transfers"""
    try:
        url = "https://api.paystack.co/transferrecipient"
        headers = {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN"
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
        
    except Exception as e:
        return {'status': False, 'message': str(e)}

def initiate_bank_transfer(amount, recipient_code, reference):
    """Initiate bank transfer to Nigerian bank account"""
    try:
        url = "https://api.paystack.co/transfer"
        headers = {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "source": "balance",
            "amount": int(amount * 100),  # Convert to kobo
            "recipient": recipient_code,
            "reference": reference
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
        
    except Exception as e:
        return {'status': False, 'message': str(e)}

def verify_transfer_status(transfer_code):
    """Verify the status of a bank transfer"""
    try:
        url = f"https://api.paystack.co/transfer/{transfer_code}"
        headers = {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        return response.json()
        
    except Exception as e:
        return {'status': False, 'message': str(e)}

def list_transfer_recipients():
    """List all transfer recipients"""
    try:
        url = "https://api.paystack.co/transferrecipient"
        headers = {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        return response.json()
        
    except Exception as e:
        return {'status': False, 'message': str(e)}

def get_banks_list():
    """Get list of Nigerian banks with codes"""
    try:
        url = "https://api.paystack.co/bank"
        headers = {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json"
        }
        
        params = {"country": "nigeria", "perPage": 100}
        response = requests.get(url, headers=headers, params=params)
        return response.json()
        
    except Exception as e:
        return {'status': False, 'message': str(e)}

def validate_bank_details(account_number, bank_code):
    """Validate bank account details"""
    try:
        url = "https://api.paystack.co/bank/resolve"
        headers = {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json"
        }
        
        params = {
            "account_number": account_number,
            "bank_code": bank_code
        }
        
        response = requests.get(url, headers=headers, params=params)
        return response.json()
        
    except Exception as e:
        return {'status': False, 'message': str(e)}
