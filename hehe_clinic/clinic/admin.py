from flask import redirect
from flask_admin.contrib.sqla import ModelView
from clinic import app, db
from flask_admin import Admin, BaseView, expose
from clinic.models import User, UserRole
from flask_login import current_user, logout_user

admin = Admin(app=app, name="Private Clinic", template_mode='bootstrap4')

class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

class MyUserView(AdminView):
    column_list = ['id', 'name', 'phone', 'username', 'email', 'address', 'user_role']
    column_searchable_list = ['username', 'name', 'phone']
    column_editable_list = ['name', ]
    can_export = True
    column_filters = ['user_role']
    column_labels = {
        'id': 'ID',
        'name': 'Họ Tên',
        'phone': 'SĐT',
        'username': 'Tên người dùng',
        'email': 'Email',
        'address': 'Địa chỉ',
        'user_role': 'Vai trò',
    }

class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated

class LogoutView(AuthenticatedView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')


admin.add_view(MyUserView(User, db.session))
admin.add_view(LogoutView(name='Đăng xuất'))