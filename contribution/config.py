import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///money_saver.db'
    PAYSTACK_SECRET_KEY = 'sk_test_4c623beabaa6f43be5fc5872756186bc764118c1'
    PAYSTACK_PUBLIC_KEY = 'pk_test_f32edffba7422d4719caf11a35ee2db5d77eb8db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('tajudeenlateef45@gmail.com')
    MAIL_PASSWORD = os.environ.get('putmein789')
    
    # Paystack settings
    PAYSTACK_SECRET_KEY = 'sk_test_4c623beabaa6f43be5fc5872756186bc764118c1'
    PAYSTACK_PUBLIC_KEY = 'pk_test_f32edffba7422d4719caf11a35ee2db5d77eb8db'
    
    # Upload settings
    UPLOAD_FOLDER = 'static/images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # App settings
    TRANSACTIONS_PER_PAGE = 10
    GOALS_PER_PAGE = 10
    
    # Admin settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
