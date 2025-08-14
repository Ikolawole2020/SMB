from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

migrate = Migrate()
admin = Admin(name='MSW', template_mode='bootstrap3')

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.email == 'admin@example.com'
    
    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for
        return redirect(url_for('main.login'))
