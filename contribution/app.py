from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
from config import Config
from models import db, User, Transaction, Goal, BankAccount, DailyGoal, Notification
from routes import main_bp
from extensions import migrate, admin
from flask_mail import Mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_user():
        if current_user.is_authenticated:
            return dict(
                current_user=current_user,
                unread_notifications=Notification.query.filter_by(
                    user_id=current_user.id, 
                    is_read=False
                ).count()
            )
        return dict()
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
