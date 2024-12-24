# file chứa các hàm xử lý gọi sử lý thêm xóa sửa, kiểm tra v..v
from sqlalchemy import func

from clinic import app, db, utils, MAX_PATIENT
from clinic.models import User, UserRole, Patient, Appointment, AppointmentList, Drug, Unit, DrugDetail, Type, Unit


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

def load_drugs(**kwargs):
    drugs = Drug.query
    name = kwargs.get('name')
    unit = kwargs.get('unit')
    type = kwargs.get('type')
    page = kwargs.get('page')

    if name:
        drugs = drugs.filter(Drug.name.contains(name))
    if unit:
        drugs = drugs.filter_by(drugUnit=unit)
    if type:
        drugs = drugs.filter_by(drugType=type)
    page_size = app.config['PAGE_SIZE']
    start = (page - 1) * page_size
    end = start + page_size
    return drugs.slice(start,end).all()

def count_drugs():
    return Drug.query.count()

def load_medical_details(**kwargs):
    pass

# def load_statics_drug():
#     info = db.session.query(
#         Drug.name.label('drug_name'),
#         Drug.quantity.label('available_quantity'),
#         func.sum(DrugDetail.quatity).label('total_used_quantity')
#     ).join(
#         DrugDetail, DrugDetail.drug == Drug.id
#     ).group_by(
#         Drug.id, Drug.name, Drug.quantity
#     ).all()
