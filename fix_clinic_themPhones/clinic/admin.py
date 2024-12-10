from flask_admin.contrib.sqla import ModelView
from clinic import app, db
from flask_admin import Admin
from clinic.models import User, UserRole, Phone
from flask_login import current_user

# Tạo Admin
admin = Admin(app=app, name="Private Clinic", template_mode='bootstrap4')


# Cấu hình lớp AuthenticatedView, chỉ cho phép ADMIN truy cập
class AuthenticatedView(ModelView):
    def is_accessible(self):
        # Kiểm tra xem người dùng đã đăng nhập và có vai trò là ADMIN không
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


# Cấu hình hiển thị cho User
class MyUserView(AuthenticatedView):
    # Các cột sẽ hiển thị trên giao diện admin
    column_list = ['id', 'name', 'phones', 'username', 'email', 'address', 'user_role']

    # Các cột có thể tìm kiếm
    column_searchable_list = ['username', 'name']

    # Các cột có thể chỉnh sửa trong admin
    column_editable_list = ['name', 'email']

    # Cho phép xuất dữ liệu
    can_export = True

    # Cột có thể lọc
    column_filters = ['user_role']

    # Định nghĩa nhãn cho các cột
    column_labels = {
        'id': 'ID',
        'name': 'Họ Tên',
        'phones': 'SĐT',
        'username': 'Tên người dùng',
        'email': 'Email',
        'address': 'Địa chỉ',
        'user_role': 'Vai trò',
    }

    # Tùy chỉnh cách hiển thị thông tin cho số điện thoại (phones)
    def _list_phones(view, context, model, name):
        # Lấy tất cả các số điện thoại liên quan đến người dùng
        phones = [phone.value for phone in model.phones]
        return ", ".join(phones)  # Nối các số điện thoại bằng dấu phẩy

    # Đăng ký phương thức này để hiển thị trong bảng
    column_formatters = {
        'phones': _list_phones
    }


admin.add_view(MyUserView(User, db.session))
