# def search_info_user(user):
#from click.decorators import P

# file chứa các hàm xử lý gọi sử lý thêm xóa sửa, kiểm tra v..v
# from tokenize import u

from clinic import app, db, utils
from clinic.models import User, UserRole, Patient, MedicalDetails, DrugDetail, Drug, Type, Doctor, Payment, \
    OnlinePayment, PaymentType, PaymentGateway, OfflinePayment


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
    # truy vấn 1 đối tượng user trong User qua id
    user = User.query.filter_by(username=username.strip()).first()
    if user and utils.auth_password(password, user.password):
        return user
    return None


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user(user_id):
    return User.query.filter(User.id == user_id).first()


def get_medicaldetails(medical_id = None):
    return MedicalDetails.query.filter(MedicalDetails.id == medical_id).first()

def get_info(user_id = None):
    query = db.session.query(MedicalDetails, Doctor, User)\
    .filter(User.id == MedicalDetails.patient_id) \
    .filter(MedicalDetails.doctor_id == Doctor.id)

    if query:
        query = query.filter(User.id == user_id).first()

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
        query = query.filter(MedicalDetails.id == medical_id)

    return query.all()


def get_payment(medical_id=None):
    query = db.session.query(MedicalDetails, Payment)\
    .filter(MedicalDetails.id == Payment.medicaldetail_id)

    if query:
       query = query.filter(MedicalDetails.id == medical_id).all()

    return query


def create_payment(date, sum, nurse_id, idGiaoDich, medical_id):
    p = OnlinePayment(date=date, sum=sum, nurse_id=nurse_id, paymentType = PaymentGateway.VNPAY, idGiaoDich = idGiaoDich,medicaldetail_id = medical_id)
    db.session.add(p)
    db.session.commit()



def add_payment(date, sum, nurse_id, medical_id, idGiaoDich, loai):
    p = None
    if loai == "radio_offline":
        p = OfflinePayment(sum = sum, nurse_id =nurse_id, medicaldetail_id = medical_id)

    else:
        p = OnlinePayment(sum = sum, nurse_id =nurse_id, medicaldetail_id = medical_id,paymentType = PaymentGateway.VNPAY)

    return p