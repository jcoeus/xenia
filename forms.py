from wtforms import Form, validators, StringField, PasswordField
from wtforms.validators import Email
from wtforms.fields.html5 import EmailField

class SignUpForm(Form):
	student_group_name = StringField('Student Group Name', validators=[validators.DataRequired()])
	email = EmailField('Email', validators=[validators.DataRequired(), validators.Length(min=6, max=35), Email("Please enter your email address.")])
	password = PasswordField('New Password', validators=[validators.DataRequired(), validators.Length(min=3, max=35), validators.EqualTo('confirm_password', message='Passwords must match')])
	confirm_password = PasswordField('Confirm Password', validators=[validators.DataRequired(), validators.Length(min=3, max=35)])

class LogInForm(Form):
	email = EmailField('Email', validators=[validators.DataRequired(), validators.Length(min=6, max=35), Email("Please enter your email address.")])
	password = PasswordField('Password', validators=[validators.DataRequired(), validators.Length(min=3, max=35)])