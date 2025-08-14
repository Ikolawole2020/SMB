from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from utils_paystack_transfer import get_banks_list, validate_bank_details
import os
import secrets
from PIL import Image
from functools import wraps
import requests
import json

from models import db, User, Transaction, Goal, BankAccount, DailyGoal, Notification
from forms import LoginForm, RegistrationForm, GoalForm, TransactionForm, BankAccountForm, ProfileForm, DailyGoalForm, DepositForm
from utils import save_picture, send_reset_email, generate_reference, verify_paystack_payment, init_paystack_payment

main_bp = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.email != 'admin@example.com':
            flash('Admin access required', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/api/nigeria-banks')
@login_required
def get_nigeria_banks():
    """API endpoint to get list of Nigeria banks"""
    try:
        banks_response = get_banks_list()
        if banks_response.get('status'):
            banks = banks_response.get('data', [])
            formatted_banks = [
                {
                    'code': bank['code'],
                    'name': bank['name']
                }
                for bank in banks
            ]
            return jsonify({'status': 'success', 'banks': formatted_banks})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to fetch banks'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/api/verify-account', methods=['POST'])
@login_required
def verify_bank_account():
    """API endpoint to verify bank account details"""
    try:
        data = request.get_json()
        account_number = data.get('account_number')
        bank_code = data.get('bank_code')
        
        if not account_number or not bank_code:
            return jsonify({'status': 'error', 'message': 'Account number and bank code required'}), 400
        
        verification_response = validate_bank_details(account_number, bank_code)
        
        if verification_response.get('status'):
            account_data = verification_response.get('data', {})
            return jsonify({
                'status': 'success',
                'account_name': account_data.get('account_name'),
                'account_number': account_data.get('account_number')
            })
        else:
            return jsonify({'status': 'error', 'message': 'Account verification failed'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Create welcome notification
        notification = Notification(
            user_id=user.id,
            title='Welcome to Money Saver!',
            message='Your account has been created successfully. Start saving today!',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        flash('Invalid email or password', 'error')
    
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    total_savings = current_user.get_total_savings()
    total_goals = current_user.get_total_goals()
    completed_goals = current_user.get_completed_goals()
    
    # Get recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Get active goals
    active_goals = Goal.query.filter_by(user_id=current_user.id, status='active')\
        .order_by(Goal.deadline.asc()).limit(3).all()
    
    # Get today's daily goal
    today = datetime.utcnow().date()
    today_goal = DailyGoal.query.filter_by(user_id=current_user.id, date=today).first()
    
    # Get notifications
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_savings=total_savings,
                         total_goals=total_goals,
                         completed_goals=completed_goals,
                         recent_transactions=recent_transactions,
                         active_goals=active_goals,
                         today_goal=today_goal,
                         notifications=notifications)

@main_bp.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('transactions.html', transactions=transactions)

@main_bp.route('/add-transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        transaction = Transaction(
            user_id=current_user.id,
            amount=form.amount.data,
            type=form.type.data,
            description=form.description.data,
            category=form.category.data,
            payment_method=form.payment_method.data,
            reference=generate_reference()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Create notification
        notification = Notification(
            user_id=current_user.id,
            title=f'{form.type.data.title()} Added',
            message=f'₦{form.amount.data:,.2f} has been {form.type.data}d successfully.',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('main.transactions'))
    
    return render_template('add_transaction.html', form=form)

@main_bp.route('/goals')
@login_required
def goals():
    page = request.args.get('page', 1, type=int)
    goals = Goal.query.filter_by(user_id=current_user.id)\
        .order_by(Goal.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('goals.html', goals=goals)

@main_bp.route('/add-goal', methods=['GET', 'POST'])
@login_required
def add_goal():
    form = GoalForm()
    if form.validate_on_submit():
        goal = Goal(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            target_amount=form.target_amount.data,
            deadline=form.deadline.data,
            category=form.category.data,
            priority=form.priority.data
        )
        
        db.session.add(goal)
        db.session.commit()
        
        # Create notification
        notification = Notification(
            user_id=current_user.id,
            title='New Goal Created',
            message=f'Your goal "{form.title.data}" has been created successfully.',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Goal created successfully!', 'success')
        return redirect(url_for('main.goals'))
    
    return render_template('add_goal.html', form=form)

@main_bp.route('/daily-goals')
@login_required
def daily_goals():
    page = request.args.get('page', 1, type=int)
    daily_goals = DailyGoal.query.filter_by(user_id=current_user.id)\
        .order_by(DailyGoal.date.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('daily_goals.html', daily_goals=daily_goals)

@main_bp.route('/add-daily-goal', methods=['GET', 'POST'])
@login_required
def add_daily_goal():
    form = DailyGoalForm()
    if form.validate_on_submit():
        daily_goal = DailyGoal(
            user_id=current_user.id,
            amount=form.amount.data,
            description=form.description.data,
            date=form.date.data
        )
        
        db.session.add(daily_goal)
        db.session.commit()
        
        flash('Daily goal added successfully!', 'success')
        return redirect(url_for('main.daily_goals'))
    
    return render_template('add_daily_goal.html', form=form)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_picture = picture_file
        
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile'))
    
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
    
    profile_image = url_for('static', filename='images/' + current_user.profile_picture)
    return render_template('profile.html', form=form, profile_image=profile_image)

@main_bp.route('/bank-accounts')
@login_required
def bank_accounts():
    accounts = BankAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('bank_accounts.html', accounts=accounts)

@main_bp.route('/add-bank-account', methods=['GET', 'POST'])
@login_required
def add_bank_account():
    form = BankAccountForm()
    if form.validate_on_submit():
        # Check if account already exists
        existing_account = BankAccount.query.filter_by(
            user_id=current_user.id,
            account_number=form.account_number.data,
            bank_code=form.bank_code.data
        ).first()
        
        if existing_account:
            flash('This bank account is already added to your profile.', 'warning')
            return redirect(url_for('main.bank_accounts'))
        
        account = BankAccount(
            user_id=current_user.id,
            
            bank_name=form.bank_name.data,
            account_number=form.account_number.data,
            account_name=form.account_name.data,
            bank_code=form.bank_code.data,
            bvn=form.bvn.data,
            is_verified=True,  # Mark as verified since it went through verification
            created_at=datetime.utcnow()
        )
        
        db.session.add(account)
        db.session.commit()
        
        # Create notification
        notification = Notification(
            user_id=current_user.id,
            title='Bank Account Added',
            message=f'Your {form.bank_name.data} account has been successfully added.',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Bank account added successfully! Your account has been verified and saved to your profile.', 'success')
        return redirect(url_for('main.bank_accounts'))
    
    return render_template('add_bank_account.html', form=form)

@main_bp.route('/api/save-verified-account', methods=['POST'])
@login_required
def save_verified_account():
    """Save verified bank account details"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['account_number', 'bank_code', 'account_name', 'bank_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required',
                    'flash': True
                }), 400
        
        # Validate account number format
        account_number = data.get('account_number', '')
        if not account_number.isdigit() or len(account_number) != 10:
            return jsonify({
                'success': False,
                'message': 'Account number must be exactly 10 digits',
                'flash': True
            }), 400
        
        # Check if account already exists
        existing_account = BankAccount.query.filter_by(
            user_id=current_user.id,
            account_number=data['account_number']
        ).first()
        
        if existing_account:
            return jsonify({
                'success': False,
                'message': 'This bank account is already added to your profile',
                'flash': True
            }), 400
        
        # Create new bank account with verified status
        account = BankAccount(
            user_id=current_user.id,
            bank_name=data['bank_name'],
            account_number=data['account_number'],
            account_name=data['account_name'],
            bank_code=data['bank_code'],
            bvn=data.get('bvn', ''),
            is_verified=True,
            created_at=datetime.utcnow()
        )
        
        db.session.add(account)
        db.session.commit()
        
        # Create notification
        notification = Notification(
            user_id=current_user.id,
            title='Bank Account Added',
            message=f'Your {data["bank_name"]} account has been successfully added and verified.',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bank account added successfully',
            'redirect_url': url_for('main.bank_accounts')
        }), 200
        
    except Exception as e:
        db.session.rollback()
        
        # Handle specific database errors
        error_message = str(e)
        if 'UNIQUE constraint failed' in error_message or 'unique constraint' in error_message.lower():
            message = 'This bank account already exists in your profile'
        elif 'FOREIGN KEY constraint failed' in error_message:
            message = 'Invalid user or bank information provided'
        elif 'NOT NULL constraint failed' in error_message:
            message = 'Missing required information. Please fill all required fields.'
        else:
            message = 'An error occurred while saving your bank account. Please try again.'
        
        return jsonify({
            'success': False,
            'message': message,
            'flash': True
        }), 500

@main_bp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    form = DepositForm()
    
    # Populate bank account choices
    accounts = BankAccount.query.filter_by(user_id=current_user.id, is_verified=True).all()
    form.bank_account_id.choices = [(account.id, f"{account.bank_name} - {account.account_number}") for account in accounts]
    
    if form.validate_on_submit():
        amount = form.amount.data
        bank_account_id = form.bank_account_id.data
        
        # Initialize Paystack payment
        payment_data = init_paystack_payment(
            email=current_user.email,
            amount=amount * 100,  # Paystack amount in kobo
            reference=generate_reference()
        )
        
        if payment_data['status']:
            # Create pending transaction
            transaction = Transaction(
                user_id=current_user.id,
                amount=amount,
                type='deposit',
                description=form.description.data or f'Deposit via bank account {bank_account_id}',
                reference=payment_data['data']['reference'],
                status='pending'
            )
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'authorization_url': payment_data['data']['authorization_url']
            })
        
        return jsonify({'status': 'error', 'message': 'Payment initialization failed'})
    
    return render_template('deposit.html', form=form, accounts=accounts)

@main_bp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        bank_account_id = request.form.get('bank_account_id')
        
        # Check if user has sufficient balance
        total_savings = current_user.get_total_savings()
        if amount > total_savings:
            return jsonify({'status': 'error', 'message': 'Insufficient balance'})
        
        # Get bank account details
        bank_account = BankAccount.query.filter_by(id=bank_account_id, user_id=current_user.id).first()
        if not bank_account:
            return jsonify({'status': 'error', 'message': 'Invalid bank account'})
        
        # Create or get recipient code for Paystack transfer
        from utils_paystack_transfer import create_transfer_recipient, initiate_bank_transfer
        
        if not bank_account.recipient_code:
            # Create recipient if not exists
            recipient_response = create_transfer_recipient(
                name=bank_account.account_name,
                account_number=bank_account.account_number,
                bank_code=bank_account.bank_code
            )
            
            if recipient_response.get('status'):
                bank_account.recipient_code = recipient_response['data']['recipient_code']
                db.session.commit()
            else:
                return jsonify({'status': 'error', 'message': 'Failed to create transfer recipient'})
        
        # Generate unique reference
        transfer_reference = generate_reference()
        
        # Initiate Paystack transfer
        transfer_response = initiate_bank_transfer(
            amount=amount,
            recipient_code=bank_account.recipient_code,
            reference=transfer_reference
        )
        
        if transfer_response.get('status'):
            # Create transaction record
            transaction = Transaction(
                user_id=current_user.id,
                amount=amount,
                type='withdrawal',
                description=f'Withdrawal to {bank_account.bank_name} - {bank_account.account_number}',
                reference=transfer_reference,
                status='pending'
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Create notification
            notification = Notification(
                user_id=current_user.id,
                title='Withdrawal Initiated',
                message=f'₦{amount:,.2f} withdrawal has been initiated to your bank account. Transfer will be processed shortly.',
                type='info'
            )
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': 'Withdrawal initiated successfully', 'transfer_reference': transfer_reference})
        else:
            return jsonify({'status': 'error', 'message': transfer_response.get('message', 'Transfer failed')})
    
    accounts = BankAccount.query.filter_by(user_id=current_user.id, is_verified=True).all()
    return render_template('withdraw.html', accounts=accounts)

@main_bp.route('/api/transfer-status/<transfer_reference>')
@login_required
def transfer_status(transfer_reference):
    """Check the status of a Paystack transfer"""
    from utils_paystack_transfer import verify_transfer_status
    
    transaction = Transaction.query.filter_by(
        reference=transfer_reference,
        user_id=current_user.id
    ).first_or_404()
    
    # Verify transfer status
    status_response = verify_transfer_status(transfer_reference)
    
    if status_response.get('status'):
        transfer_data = status_response.get('data', {})
        
        # Update transaction status based on transfer status
        if transfer_data.get('status') == 'success':
            transaction.status = 'completed'
            transaction.completed_at = datetime.utcnow()
            
            # Create success notification
            notification = Notification(
                user_id=current_user.id,
                title='Withdrawal Completed',
                message=f'₦{transaction.amount:,.2f} has been successfully transferred to your bank account.',
                type='success'
            )
            db.session.add(notification)
            
        elif transfer_data.get('status') == 'failed':
            transaction.status = 'failed'
            
            # Create failure notification
            notification = Notification(
                user_id=current_user.id,
                title='Withdrawal Failed',
                message=f'Withdrawal of ₦{transaction.amount:,.2f} failed. Please try again.',
                type='error'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'transfer_status': transfer_data.get('status'),
            'message': transfer_data.get('reason', '')
        })
    
    return jsonify({'status': 'error', 'message': 'Unable to verify transfer status'})

@main_bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    # Mark all as read
    if request.args.get('mark_all_read'):
        Notification.query.filter_by(user_id=current_user.id, is_read=False)\
            .update({'is_read': True})
        db.session.commit()
        flash('All notifications marked as read', 'success')
        return redirect(url_for('main.notifications'))
    
    return render_template('notifications.html', notifications=notifications)

@main_bp.route('/api/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    if not notification.is_read:
        notification.is_read = True
        db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/api/notifications/unread-count')
@login_required
def unread_notifications_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

@main_bp.route('/api/goals/<int:goal_id>/progress')
@login_required
def goal_progress(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'progress': goal.get_progress_percentage(),
        'current_amount': goal.current_amount,
        'target_amount': goal.target_amount
    })

@main_bp.route('/api/transactions/summary')
@login_required
def transactions_summary():
    # Get summary for current month
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    deposits = Transaction.query.filter_by(
        user_id=current_user.id,
        type='deposit',
        status='completed'
    ).filter(Transaction.created_at >= start_of_month).all()
    
    withdrawals = Transaction.query.filter_by(
        user_id=current_user.id,
        type='withdrawal',
        status='completed'
    ).filter(Transaction.created_at >= start_of_month).all()
    
    total_deposits = sum(t.amount for t in deposits)
    total_withdrawals = sum(t.amount for t in withdrawals)
    
    return jsonify({
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'net_savings': total_deposits - total_withdrawals
    })

@main_bp.route('/api/verify-payment/<reference>', methods=['POST'])
@login_required
def verify_payment(reference):
    """Verify Paystack payment and update transaction"""
    try:
        # Verify payment with Paystack
        verification_response = verify_paystack_payment(reference)
        
        if verification_response['status']:
            payment_data = verification_response['data']
            
            # Find the transaction
            transaction = Transaction.query.filter_by(
                reference=reference,
                user_id=current_user.id
            ).first()
            
            if transaction:
                if payment_data['status'] == 'success':
                    # Update transaction status
                    transaction.status = 'completed'
                    transaction.completed_at = datetime.utcnow()
                    
                    # Create success notification
                    notification = Notification(
                        user_id=current_user.id,
                        title='Deposit Successful',
                        message=f'₦{transaction.amount:,.2f} has been deposited successfully to your account.',
                        type='success'
                    )
                    db.session.add(notification)
                    db.session.commit()
                    
                    return jsonify({'status': 'success', 'message': 'Payment verified successfully'})
                else:
                    # Mark transaction as failed
                    transaction.status = 'failed'
                    db.session.commit()
                    
                    return jsonify({'status': 'error', 'message': 'Payment failed'})
            else:
                return jsonify({'status': 'error', 'message': 'Transaction not found'})
        else:
            return jsonify({'status': 'error', 'message': 'Payment verification failed'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
