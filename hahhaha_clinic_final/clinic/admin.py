import math

from flask import redirect, request, url_for
from flask_admin.contrib.sqla import ModelView
from clinic import app, db, utils
from flask_admin import Admin, BaseView, expose
from clinic.models import User, UserRole, Doctor, Nurse, Patient, Type, Unit, Drug
from flask_login import current_user, logout_user
from clinic import dao
from datetime import datetime

admin = Admin(app=app, name="SaiGon Care", template_mode='bootstrap4')


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

class AdminBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class MyUserView(AdminView):
    column_list = ['id', 'name', 'phone', 'username', 'email', 'address', 'user_role']
    column_searchable_list = ['username', 'name', 'phone']
    column_editable_list = ['name', ]
    can_export = True
    column_filters = ['user_role']
    # Thêm phân trang
    page_size = 4
    can_set_page_size = True
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

class DrugType(AdminView):
    column_list = ['id', 'name', 'create_date', 'update_date']
    column_searchable_list = ['id', 'name']
    column_editable_list = ['name']
    column_filters = ['name']
    page_size = 4
    can_set_page_size = True
    # Loại trừ các trường không được chỉnh sửa
    form_excluded_columns = ['create_date', 'update_date']
    column_labels = {
        'id': 'ID',
        'name': 'Tên loại thuốc',
        'create_date' : 'Ngày tạo',
        'update_date': 'Ngày cập nhập'
    }

class DrugUnit(AdminView):
        column_list = ['id', 'name', 'create_date', 'update_date']
        column_searchable_list = ['id', 'name']
        column_editable_list = ['name']
        column_filters = ['name']
        page_size = 4
        can_set_page_size = True
        # Loại trừ các trường không được chỉnh sửa
        form_excluded_columns = ['create_date', 'update_date']
        column_labels = {
            'id': 'ID',
            'name': 'Tên đơn vị',
            'create_date': 'Ngày tạo',
            'update_date': 'Ngày cập nhập'
        }

class DrugManagement(AdminBaseView):
    @expose('/')
    def index(self):
        name = request.args.get('name')
        unit = request.args.get('unit')
        type = request.args.get('type')
        page = request.args.get('page',1)
        counter = dao.count_drugs()
        drugs = dao.load_drugs(
            name=name,
            unit=unit,
            type=type,
            page=int(page)
        )

        return self.render('admin/drug_management.html',
                           drugs=drugs,
                           drugTypes=Type.query.all(),
                           drugUnits=Unit.query.all(),
                           page=math.ceil(counter / app.config['PAGE_SIZE'])
                           )

        # Thêm mới thuốc

    @expose('/add', methods=['GET', 'POST'])
    def add_drug(self):
        if request.method == 'POST':
            name = request.form['name']
            drug_type = request.form['drugType']
            drug_unit = request.form['drugUnit']
            price = request.form['price']
            quantity = request.form['quantity']

            new_drug = Drug(name=name, drugType=drug_type, drugUnit=drug_unit, price=price, quantity=quantity)
            db.session.add(new_drug)
            db.session.commit()
            return redirect(url_for('drugmanagement.index'))

        drug_types = Type.query.all()
        drug_units = Unit.query.all()
        return self.render('admin/add_drug.html', drugTypes=drug_types, drugUnits=drug_units)

    @expose('/delete/<int:drug_id>', methods=['POST'])
    def delete_drug(self, drug_id):
        drug = Drug.query.get_or_404(drug_id)
        db.session.delete(drug)
        db.session.commit()
        return redirect(url_for('drugmanagement.index'))

    @expose('/edit/<int:drug_id>', methods=['GET', 'POST'])
    def edit_drug(self, drug_id):
        drug = Drug.query.filter_by(id=drug_id).first()
        if request.method == 'POST':
            drug.name = request.form['name']
            drug.drugType = request.form['drugType']
            drug.drugUnit = request.form['drugUnit']
            drug.price = request.form['price']
            drug.quantity = request.form['quantity']
            db.session.commit()
            return redirect(url_for('drugmanagement.index'))

        drug_types = Type.query.all()
        drug_units = Unit.query.all()
        return self.render('admin/edit_drug.html', drug=drug, drugTypes=drug_types, drugUnits=drug_units)

class StatisticsReport(AdminBaseView):
    @expose('/')
    def index(self):
        year = request.args.get('year',"")
        month = request.args.get('month',"")

        try:
            year = int(year)
            month = int(month)
        except (TypeError, ValueError):
            year = datetime.now().year
            month = datetime.now().month

        # Lấy thống kê theo tháng và năm
        monthly_stats = dao.products_month_stats(year=year)
        revenue_patient_stats = dao.get_revenue_patient_stats(month=month, year=year)
        medicine_usage = dao.get_medicine_usage_stats(month=month, year=year)

        return self.render('admin/statistics_report.html',
                           month_stats=monthly_stats,
                           revenue_patient_stats=revenue_patient_stats,
                           medicine_usage=medicine_usage,
                           selected_month=month,
                           selected_year=year)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


admin.add_view(MyUserView(User, db.session))
admin.add_view(DrugManagement(name='Quản Lý Thuốc'))
admin.add_view(StatisticsReport(name='Thống kê báo cáo'))
admin.add_view(DrugType(Type, db.session, name='Loại Thuốc'))
admin.add_view(DrugUnit(Unit, db.session, name='Đơn vị'))
admin.add_view(LogoutView(name='Đăng xuất'))
