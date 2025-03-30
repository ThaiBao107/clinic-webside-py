#file này để test những trường hợp mới

from itsdangerous.serializer import Serializer
from clinic import app
#
# serial = Serializer(app.secret_key)
# token=serial.dumps({'user_id':3}).encode('utf-8')
# print(f" Token mã hóa {token}")
# # Tạo Serializer
# serial = Serializer(app.secret_key)
#
# # Token bạn muốn giải mã
# token = b'{"user_id": 3}.tDNES17kFNnklNX0PG0j6ZIuj1w'
#
# try:
#     # Giải mã token
#     data = serial.loads(token)
#     print("User ID:", data['user_id'])
# except Exception as e:
#     print("Error decoding token:", e)

