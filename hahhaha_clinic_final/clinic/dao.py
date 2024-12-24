# file chứa các hàm xử lý gọi sử lý thêm xóa sửa, kiểm tra v..v
from datetime import datetime

from sqlalchemy import func

from clinic import app, db, utils, MAX_PATIENT
from clinic.models import User, UserRole, Patient, Appointment, AppointmentList, Drug, Unit, DrugDetail, Type, Unit, MedicalDetails, Payment, OnlinePayment, OfflinePayment \
    , Doctor, PaymentGateway,Condition


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




def get_user(user_id):
    return User.query.filter(User.id == user_id).first()


def get_medicaldetails(medical_id = None):
    return MedicalDetails.query.filter(MedicalDetails.id == medical_id).first()


#Moi sua
def get_info(user_id = None):
    query = db.session.query(MedicalDetails, Doctor, User)\
    .filter(User.id == MedicalDetails.patient_id) \
    .filter(MedicalDetails.doctor_id == Doctor.id)

    if query:
        query = query.filter(User.id == user_id).all()
        print(query)
        for k in query:
            total_paid = payment_total(medical_id=k[0].id)
            print("total")
            print(total_paid)
            m= MedicalDetails.query.get(k[0].id)
            total_medical = utils.total(medical_id=k[0].id)
            print(total_medical)
            if total_medical - total_paid <= 0:
                continue
            else:
                query = k
                break

        print("All phieu kham benh")
        print(query)


    return query

def payment_total(medical_id=None):
    total = 0
    print(medical_id)
    query = Payment.query.filter(Payment.medicalDetail_id == medical_id).all()
    print(query)
    if query:
        for p in query:
            if p.trangthai.__eq__("Condition.PAID"):
                total += int(p.sum)
    return total

def get_payment(medical_id=None):
    query = db.session.query(MedicalDetails, Payment)\
    .filter(MedicalDetails.id == Payment.medicalDetail_id)

    if query:
       query = query.filter(MedicalDetails.id == medical_id).all()

    return query


def get_drugDetail(medicalDetails_id=None):
    query = db.session.query(DrugDetail, Drug, MedicalDetails, Type ) \
        .filter(MedicalDetails.id == DrugDetail.medicalDetails) \
        .filter(DrugDetail.drug == Drug.id) \
        .filter(Drug.drugType == Type.id)

    if medicalDetails_id:
        query = query.filter(MedicalDetails.id == medicalDetails_id)
    return query.all()


def get_pay(medical_id =None):
    query = db.session.query(Drug, DrugDetail, MedicalDetails)\
    .filter(DrugDetail.drug == Drug.id) \
    .filter(MedicalDetails.id == DrugDetail.medicalDetails)
    if query:
        print("Do get pay")
        query = query.filter(MedicalDetails.id == medical_id)

    return query.all()






def get_Payment2(medical_id=None):
    query = db.session.query(MedicalDetails, Payment) \
        .filter(MedicalDetails.id == Payment.medicalDetail_id)
    if query:
        query = query.filter(MedicalDetails.id == medical_id).all()
        print(query)
        for p in query:
            if p[1].trangthai.__eq__("Condition.UNPAID"):
                print(p[1].id)
                return p[1].id
    return None


def get_only_payment(payment_id = None):
    return Payment.query.filter(Payment.id == payment_id).first()



def create_payment(date, sum, nurse_id, idGiaoDich, medical_id):
    p = OnlinePayment(date=date, sum=sum, nurse_id=nurse_id, paymentType = PaymentGateway.VNPAY, idGiaoDich = idGiaoDich,medicaldetail_id = medical_id)
    db.session.add(p)
    db.session.commit()



def add_payment(date, sum, nurse_id, medical_id, idGiaoDich, loai):
    p = None
    if loai == "radio_offline":
        p = OfflinePayment(date = datetime.now() ,sum = sum, nurse_id =nurse_id, medicalDetail_id = medical_id, trangthai = Condition.PAID)

    else:
        p = OnlinePayment(date = datetime.now() ,sum = sum, nurse_id =nurse_id, medicalDetail_id = medical_id, paymentType = PaymentGateway.VNPAY
                          ,trangthai = Condition.UNPAID)

    return p



def get_online_payment(payment_id = None):
    return OnlinePayment.query.filter(OnlinePayment.id == payment_id).first()






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
