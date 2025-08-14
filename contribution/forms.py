from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField, DateField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from flask_wtf.file import FileAllowed
from wtforms.fields import EmailField, TelField

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = TelField('Phone Number', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class GoalForm(FlaskForm):
    title = StringField('Goal Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    target_amount = FloatField('Target Amount', validators=[DataRequired(), NumberRange(min=1)])
    deadline = DateField('Deadline', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('emergency', 'Emergency Fund'),
        ('vacation', 'Vacation'),
        ('car', 'Car Purchase'),
        ('house', 'House Purchase'),
        ('education', 'Education'),
        ('business', 'Business'),
        ('wedding', 'Wedding'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Goal')

class TransactionForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=1)])
    type = SelectField('Type', choices=[
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    category = SelectField('Category', choices=[
        ('salary', 'Salary'),
        ('gift', 'Gift'),
        ('business', 'Business'),
        ('investment', 'Investment'),
        ('refund', 'Refund'),
        ('other', 'Other'),
        ('bills', 'Bills'),
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('shopping', 'Shopping'),
        ('entertainment', 'Entertainment')
    ], validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card Payment'),
        ('cash', 'Cash')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Transaction')

class BankAccountForm(FlaskForm):
    bank_code = SelectField('Bank', choices=[], validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=10, max=10)])
    account_name = StringField('Account Name', validators=[DataRequired(), Length(max=100)])
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=100)])
    bvn = StringField('BVN', validators=[Optional(), Length(min=11, max=11)])
    submit = SubmitField('Add Bank Account')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = TelField('Phone Number', validators=[Optional(), Length(max=20)])
    picture = FileField('Update Profile Picture', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')

class DailyGoalForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Add Daily Goal')

class DepositForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    category = SelectField('Category', choices=[
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal')
    ], validators=[DataRequired()])
    bank_account_id = SelectField('Bank Account', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Deposit')

