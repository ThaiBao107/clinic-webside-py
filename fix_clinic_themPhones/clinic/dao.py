# file chứa các hàm xử lý gọi sử lý thêm xóa sửa, kiểm tra v..v
from clinic import app, db, utils, MAX_PATIENT
from clinic.models import User, UserRole, Patient, Appointment, Phone


def add_user(name, username, password, **kwargs):
    password = utils.hash_password(password)
    user_role = kwargs.get('user_role', UserRole.PATIENT)

    # Tạo đối tượng user
    user = User(
        name=name.strip(),
        username=username.strip(),
        password=password,
        email=kwargs.get('email'),
        avatar=kwargs.get('avatar'),
        gender=kwargs.get('gender'),
        dob=kwargs.get('dob'),
        address=kwargs.get('address'),
        user_role=user_role,
    )
    db.session.add(user)
    db.session.commit()
    phone = kwargs.get('phone')
    if phone:
        phone_obj = Phone(value=phone, user_id=user.id)
        db.session.add(phone_obj)
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

    appoint = Appointment(
        description= kwargs.get('description'),
        schedule_date = kwargs.get('schedule_date'),
        schedule_time = kwargs.get('schedule_time'),
        patient_id = kwargs.get('patient_id')
        # do y tá chưa phải là người xuất danh sách nên id_appointmentList hiện tại là null
    )
    db.session.add(appoint)
    db.session.commit()





