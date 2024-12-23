# file chứa các hàm xử lý gọi sử lý thêm xóa sửa, kiểm tra v..v
from pyexpat.errors import messages

from clinic import app, db, utils, MAX_PATIENT
from clinic.models import User, UserRole, Patient, Appointment, AppointmentList, MedicalDetails,Drug, Unit,Type, CategoriesDrug
from flask import render_template, request, url_for, redirect, flash, jsonify, session, make_response
from flask_login import login_user, logout_user, login_required, current_user


def add_user(name, username, password, **kwargs):
    password = utils.hash_password(password)
    user_role = kwargs.get('user_role', UserRole.PATIENT)  # Lấy vai trò từ kwargs hoặc đặt mặc định là PATIENT
    user = User(
        name=name.strip(),
        username=username.strip(),
        password=password,
        email=kwargs.get('email'),
        avatar=kwargs.get('avatar'),
        gender=kwargs.get('gender'),
        dob=kwargs.get('dob'),
        address=kwargs.get('address'),
        phone=kwargs.get('phone'),
        user_role=user_role
    )
    db.session.add(user)
    db.session.commit()
    patient = Patient(id=user.id)
    db.session.add(patient)
    db.session.commit()

def check_login(username, password, role=UserRole.PATIENT):
   #truy vấn 1 đối tượng user trong User qua id
    user = User.query.filter_by(username=username.strip()).first()
    if user and utils.auth_password(password,user.password):
        return user
    return None

def get_user_by_id(user_id):
    return User.query.get(user_id)

def existing_appointment(schedule_date, schedule_time):
    existing_app = Appointment.query.filter_by(schedule_time=schedule_time,
                                               schedule_date=schedule_date).first()
    if existing_app:
        return True
    return False

def check_max_patients_for_a_day(schedule_date):
    if not schedule_date:
        return False
    patient_count = Appointment.query.filter_by(schedule_date=schedule_date).count()
    if patient_count < MAX_PATIENT:
        return False
    return True

def add_appointment(**kwargs):
    appointment_list = AppointmentList.query.filter_by(schedule_date=kwargs.get('schedule_date')).first()
    appoint = Appointment(
        description= kwargs.get('description'),
        schedule_date = kwargs.get('schedule_date'),
        schedule_time = kwargs.get('schedule_time'),
        patient_id = kwargs.get('patient_id'),
        appointment_list_id = appointment_list.id if appointment_list else None
    )
    db.session.add(appoint)
    db.session.commit()

def get_patient_appointment(patient_id):

    patient = (
        db.session.query(User, Appointment)
        .join(Appointment, Appointment.patient_id == User.id)
        .filter(User.id == patient_id)
        .first()
    )
    return patient

def load_unit():
    return Unit.query.all()

def load_type():
    return Type.query.all()


def load_drugs(**kwargs):
        drugs = Drug.query
        name = kwargs.get('name')
        unit = kwargs.get('unit')
        type = kwargs.get('type')

        if name:
            drugs = drugs.filter(Drug.name.contains(name))
        if unit:
            drugs = drugs.filter_by(drugUnit=unit)
        if type:
            drugs = drugs.filter_by(drugType=type)


def get_drug_by_id(drug_id):
    return Drug.query.get(drug_id)

def get_unit_by_id(unit_id):
    return Unit.query.get(unit_id)

def get_drug_by_name(drug_name=None):
    if not drug_name:
        return None  # Nếu không có tên thuốc, trả về None

    # Truy vấn thuốc theo tên
    drug = Drug.query.filter(Drug.name == drug_name).first()

    # Kiểm tra nếu tìm thấy thuốc
    if drug:
        return drug  # Trả về đối tượng thuốc
    else:
        return None

def get_type_by_drug_id(drug_id):
    # Join bảng Drug với Type để lấy thông tin Type
    drug_type = db.session.query(Type)\
        .join(Drug, Drug.drugType == Type.id)\
        .filter(Drug.id == drug_id)\
        .first()
    return drug_type

def get_unit_by_drug_id(drug_id):
    # Join bảng Drug với Unit để lấy thông tin Unit
    drug_unit = db.session.query(Unit)\
        .join(Drug, Drug.drugUnit == Unit.id)\
        .filter(Drug.id == drug_id)\
        .first()
    return drug_unit