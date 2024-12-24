import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv

load_dotenv()  # Tải các biến môi trường từ file .env

app = Flask(__name__)
app.secret_key = "KJGHJG^&*%&*^T&*(IGFG%ERFTGHCFHGF^&**&TYIU"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:bao1072004@localhost/clinic1?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_USERNAME'] = "phongkhamsaigoncare@gmail.com"
app.config['MAIL_PASSWORD'] = "picuqcqvzsvgplyk"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_PORT'] = 587
app.config['SUM'] = 100000

mail = Mail(app)

db = SQLAlchemy(app=app)

cloudinary.config(
       cloud_name = 'dmz9kuzue',
       api_key = '961193598266337',
       api_secret = 'yWKRKcoNtsmwsdpYhVbosl5X8Ng'
)

login = LoginManager(app=app)

VNPAY_RETURN_URL = os.environ.get('VNPAY_RETURN_URL')
VNPAY_PAYMENT_URL = os.environ.get('VNPAY_PAYMENT_URL')
VNPAY_API_URL = os.environ.get('VNPAY_API_URL')
VNPAY_TMN_CODE = os.environ.get('VNPAY_TMN_CODE')
VNPAY_HASH_SECRET_KEY = os.environ.get('VNPAY_HASH_SECRET_KEY')
MAX_PATIENT = 3
