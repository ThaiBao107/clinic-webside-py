#file này xử lý xác thực liên quan tới form - thư viện wtforms
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class ResetPasswordForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired()])
    submit = SubmitField(label='Request Email', validators=[DataRequired()])

class ChangePasswordForm(FlaskForm):
    password = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired()])
    submit = SubmitField(label='Change Password', validators=[DataRequired()])

