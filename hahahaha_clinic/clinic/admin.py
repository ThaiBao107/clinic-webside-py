from flask import redirect
from flask_admin.contrib.sqla import ModelView
from clinic import app, db, utils
from flask_admin import Admin, BaseView, expose
from clinic.models import User, UserRole, Doctor, Nurse, Patient
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

    def on_model_change(self, form, model, is_created):
        if 'password' in form:
            password = form.password.data
            if password:
                hashed_password = utils.hash_password(password)
                model.password = hashed_password

        if is_created:
            db.session.add(model)
            db.session.commit()
            if model.user_role == UserRole.DOCTOR:
                doctor = Doctor(id=model.id, specialization="Chưa cập nhật", degree="Chưa cập nhật", experience="0")
                db.session.add(doctor)

            elif model.user_role == UserRole.NURSE:
                nurse = Nurse(id=model.id)
                db.session.add(nurse)

            elif model.user_role == UserRole.PATIENT:
                patient = Patient(id=model.id)
                db.session.add(patient)

            db.session.commit()
        else:
            # Nếu không phải tạo mới, gọi hàm gốc để xử lý
            super().on_model_change(form, model, is_created)

    def delete_model(self, model):
        """
        Ghi đè phương thức xóa để xử lý dữ liệu liên quan trước khi xóa user.
        """
        try:
            # Xóa dữ liệu liên quan trong bảng Doctor, Nurse, Patient
            if model.user_role == UserRole.DOCTOR:
                doctor = Doctor.query.filter_by(id=model.id).first()
                if doctor:
                    db.session.delete(doctor)

            elif model.user_role == UserRole.NURSE:
                nurse = Nurse.query.filter_by(id=model.id).first()
                if nurse:
                    db.session.delete(nurse)

            elif model.user_role == UserRole.PATIENT:
                patient = Patient.query.filter_by(id=model.id).first()
                if patient:
                    db.session.delete(patient)

            # Xóa chính user đó
            db.session.delete(model)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            return False


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
