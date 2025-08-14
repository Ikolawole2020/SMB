import os
import secrets
from PIL import Image
from flask import current_app, url_for
from flask_mail import Message
from paystackapi.paystack import Paystack
from paystackapi.transaction import Transaction as PaystackTransaction
import requests
import random
import string

def save_picture(form_picture):
    """Save uploaded profile picture and return filename"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/images', picture_fn)
    
    # Resize image
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

def send_reset_email(user):
    """Send password reset email"""
    from app import mail
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('main.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

def generate_reference():
    """Generate unique reference for transactions"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def init_paystack_payment(email, amount, reference):
    """Initialize Paystack payment"""
    paystack = Paystack(secret_key=current_app.config['sk_test_4c623beabaa6f43be5fc5872756186bc764118c1'])
    
    try:
        response = paystack.transaction.initialize(
            email=email,
            amount=amount,
            reference=reference
        )
        return response
    except Exception as e:
        return {'status': False, 'message': str(e)}

def verify_paystack_payment(reference):
    """Verify Paystack payment"""
    paystack = Paystack(secret_key=current_app.config['sk_test_4c623beabaa6f43be5fc5872756186bc764118c1/'])
    
    try:
        response = paystack.transaction.verify(reference)
        return response
    except Exception as e:
        return {'status': False, 'message': str(e)}

def format_currency(amount):
    """Format amount as currency"""
    return f"₦{amount:,.2f}"

def calculate_savings_rate(income, savings):
    """Calculate savings rate percentage"""
    if income <= 0:
        return 0
    return (savings / income) * 100

def get_monthly_summary(user_id, year=None, month=None):
    """Get monthly financial summary"""
    from models import Transaction
    from datetime import datetime
    
    if year is None:
        year = datetime.utcnow().year
    if month is None:
        month = datetime.utcnow().month
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date,
        Transaction.status == 'completed'
    ).all()
    
    total_deposits = sum(t.amount for t in transactions if t.type == 'deposit')
    total_withdrawals = sum(t.amount for t in transactions if t.type == 'withdrawal')
    
    return {
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'net_savings': total_deposits - total_withdrawals,
        'transaction_count': len(transactions)
    }

def get_financial_insights(user_id):
    """Generate financial insights for user"""
    from models import Transaction, Goal
    
    # Get recent transactions
    recent_transactions = Transaction.query.filter_by(
        user_id=user_id,
        status='completed'
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Calculate spending patterns
    categories = {}
    for transaction in recent_transactions:
        if transaction.type == 'withdrawal':
            if transaction.category in categories:
                categories[transaction.category] += transaction.amount
            else:
                categories[transaction.category] = transaction.amount
    
    # Get goal progress
    goals = Goal.query.filter_by(user_id=user_id).all()
    total_goals = len(goals)
    completed_goals = len([g for g in goals if g.status == 'completed'])
    
    # Calculate savings rate
    total_deposits = sum(t.amount for t in recent_transactions if t.type == 'deposit')
    total_withdrawals = sum(t.amount for t in recent_transactions if t.type == 'withdrawal')
    
    savings_rate = calculate_savings_rate(total_deposits + total_withdrawals, total_deposits)
    
    return {
        'top_spending_categories': dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]),
        'total_goals': total_goals,
        'completed_goals': completed_goals,
        'savings_rate': savings_rate,
        'recent_activity': len(recent_transactions)
    }

def validate_bank_account(account_number, bank_code):
    """Validate bank account using Paystack"""
    paystack = Paystack(secret_key=current_app.config['sk_test_4c623beabaa6f43be5fc5872756186bc764118c1'])
    
    try:
        response = paystack.verification.resolve_account(
            account_number=account_number,
            bank_code=bank_code
        )
        return response
    except Exception as e:
        return {'status': False, 'message': str(e)}

def get_banks_list():
    """Get list of Nigerian banks"""
    paystack = Paystack(secret_key=current_app.config['sk_test_4c623beabaa6f43be5fc5872756186bc764118c1'])
    
    try:
        response = paystack.misc.list_banks()
        return response
    except Exception as e:
        return {'status': False, 'message': str(e)}

def send_sms_notification(phone, message):
    """Send SMS notification (placeholder for SMS service integration)"""
    # This is a placeholder for SMS service integration
    # You can integrate with services like Twilio, Africa's Talking, etc.
    return True

def generate_report(user_id, report_type='monthly'):
    """Generate financial report"""
    from models import Transaction, Goal
    from datetime import datetime, timedelta
    
    if report_type == 'monthly':
        start_date = datetime.utcnow().replace(day=1)
        end_date = datetime.utcnow()
    elif report_type == 'weekly':
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
    elif report_type == 'yearly':
        start_date = datetime.utcnow().replace(month=1, day=1)
        end_date = datetime.utcnow()
    
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date,
        Transaction.status == 'completed'
    ).all()
    
    goals = Goal.query.filter(
        Goal.user_id == user_id,
        Goal.created_at >= start_date,
        Goal.created_at <= end_date
    ).all()
    
    return {
        'transactions': transactions,
        'goals': goals,
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date
    }
