# file này xử lý về vấn đề xử lý thông tin người dùng
import bcrypt

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.strip().encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def auth_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))