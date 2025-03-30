import bcrypt
from sqlalchemy.testing.plugin.plugin_base import config
from clinic import app

from clinic import dao


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.strip().encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def auth_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def total(medical_id = None):
    drugdetail = dao.get_pay(medical_id)
    print("hello")
    print(drugdetail)
    sum = 0
    for item in drugdetail:
        sum += float(item[0].price) * item[1].quantity
    sum += app.config['SUM']
    return sum




