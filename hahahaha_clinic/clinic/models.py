from enum import Enum as UserEnum
from enum import Enum as PaymentOnline
from sqlalchemy import DateTime, Enum, Column, Integer, String, Float, Boolean, ForeignKey, Date, func, Time, Double
from sqlalchemy.orm import relationship
from clinic import app, db, utils
from  datetime import datetime, date
from flask_login import UserMixin
from itsdangerous.url_safe import URLSafeSerializer as Serializer


class UserRole(UserEnum):
    ADMIN = 'admin'
    PATIENT = 'patient'
    NURSE = 'nurse'
    DOCTOR = 'doctor'

class Gender(UserEnum):
    MALE = 'male'
    FEMALE = 'female'

class PaymentType(PaymentOnline):
    MOMO = 'momo'
    VNPAY = 'vnpay'

class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(70), nullable=False)
    avatar = Column(String(255))
    email = Column(String(50))
    user_role = Column(Enum(UserRole), nullable=False)
    gender = Column(Enum(Gender))
    address = Column(String(255), default='HoChiMinh')
    dob = Column(Date, default=date.today)
    phone = Column(String(20), nullable=False)

    def get_token(self):
        serial=Serializer(app.secret_key)
        return serial.dumps({'user_id':self.id})

    @staticmethod
    def verify_token(token):
        serial = Serializer(app.secret_key)
        try:
            user_id = serial.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


    def __str__(self):
        return self.name

class Doctor(db.Model):
    __tablename__ = 'Doctor'
    id = Column(Integer, ForeignKey('User.id'),primary_key= True )
    specialization = Column(String(50), nullable=False)
    degree = Column(String(50), nullable=False)
    experience = Column(String(50), nullable=False)
    medicalDetails = relationship('MedicalDetails', backref='doctor', lazy=True)

class Admin(db.Model):
    __tablename__ = 'Admin'
    id = Column(Integer, ForeignKey('User.id'), primary_key=True)
    categoriesDrugList = relationship('CategoriesDrug', backref='admin', lazy=True)


class Patient(db.Model):
    __tablename__ = 'Patient'
    id = Column(Integer, ForeignKey('User.id'), primary_key=True)
    appointments = relationship('Appointment', backref='patient', lazy=True)
    medicalDetails = relationship('MedicalDetails', backref='patient', lazy=True)


class Nurse(db.Model):
    __tablename__ = 'Nurse'
    id = Column(Integer, ForeignKey('User.id'), primary_key=True)
    appointmentLists = relationship('AppointmentList', backref='nurse', lazy=True)
    payments = relationship('Payment', backref='nurse', lazy=True)

class Payment(db.Model):
    __tablename__ = 'Payment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=date.today)
    sum = Column(String(20), nullable=False)
    nurse_id = Column(Integer, ForeignKey('Nurse.id'), nullable=False)
    medicalDetail_id = Column(Integer, ForeignKey('MedicalDetails.id'), nullable=False)

class MedicalDetails(db.Model):
    __tablename__ = 'MedicalDetails'
    id =Column(Integer, primary_key=True, autoincrement=True)
    diagnose = Column(String(50), nullable=False)
    symptoms= Column(String(50), nullable=False)
    doctor_id = Column(Integer, ForeignKey('Doctor.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('Patient.id'), nullable=False)
    payments = relationship('Payment', backref='MedicalDetails', lazy=True)
    drugs = relationship(
        'Drug',
        secondary='DrugDetail',
        backref=db.backref('DrugDetail', lazy='dynamic'),
        lazy='dynamic'
    )


class OnlinePayment(Payment):
    id = Column(Integer, ForeignKey('Payment.id'), nullable=False, primary_key=True)
    paymentType = Column(Enum(PaymentType), nullable=False)
    idGiaoDich = Column(String(50), nullable=False)


class OfflinePayment(Payment):
    id = Column(Integer, ForeignKey('Payment.id'), nullable=False, primary_key=True)


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    create_date = Column(DateTime, default=func.now())
    update_date = Column(DateTime, default=func.now(), onupdate=func.now())

class AppointmentList(BaseModel):
    __tablename__ = 'AppointmentList'
    schedule_date = Column(Date, unique=True)
    nurse_id = Column(Integer, ForeignKey('Nurse.id'), nullable=False)
    appointments = relationship('Appointment', backref='Appointment_list', lazy=True)

class Status(UserEnum):
    PENDING = 'pending' #Chờ xác nhận
    CONFIRMED = 'confirmed' #đã xác nhận
    CANCELED = 'canceled' # bị hủy
    COMPLETED = 'completed'  # Đã khám bệnh - bác sĩ tự xác nhận

class Appointment(BaseModel):
    __tablename__ = 'Appointment'
    description = Column(String(255), nullable=False) #Vấn đề cần khám
    status = Column(Enum(Status), default=Status.PENDING) #mặc định ban đầu
    schedule_date = Column(Date, nullable=False)
    schedule_time = Column(Time, nullable=False )
    patient_id = Column(Integer, ForeignKey(Patient.id), nullable=False)
    appointment_list_id = Column(Integer, ForeignKey(AppointmentList.id), nullable=True)

    def __str__(self):
        return (f"Lịch khám ngày {self.schedule_date},"
                f" thời gian {self.schedule_time},"
                f" trạng thái {self.status}")


class Unit(db.Model):
    __tablename__ = 'Unit'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)


class Type(db.Model):
    __tablename__ = 'Type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

class Drug(db.Model):
    __tablename__ = 'Drug'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    price = Column(String(20), nullable=False)
    drugType = Column(Integer, ForeignKey('Type.id'),nullable=False)
    drugUnit = Column(Integer,ForeignKey('Unit.id'), nullable=False)
    quantity = Column(Double, nullable=False)
    category_id = Column(Integer, ForeignKey('CategoriesDrug.id'), nullable=False)


class CategoriesDrug(db.Model):
    __tablename__ = 'CategoriesDrug'
    id = Column(Integer, primary_key=True, autoincrement=True)
    drugs = relationship('Drug', backref='CategoriesDrug', lazy=True)
    admin_id = Column(Integer, ForeignKey('Admin.id'), nullable=False)


class DrugDetail(db.Model):
    __tablename__ = 'DrugDetail'
    id = Column(Integer, primary_key=True, autoincrement=True)
    medicalDetails_id = Column(Integer, ForeignKey('MedicalDetails.id') , nullable=False)
    drug_id = Column(Integer,ForeignKey('Drug.id'), nullable=False)
    medication_instructions= Column(String(255), nullable=False)
    quatity = Column( Double, nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tạo các bảng trong cơ sở dữ liệu
        db.session.commit()

        #Existing admin, patient, nurse entries

        # payment1 = OfflinePayment(date = date(day=10, month=5, year=2024), sum = 200000, nurse_id = n4.id)
        # db.session.add(payment1)
        # db.session.commit()
        # m1 = MedicalDetails(diagnose = "Đau vai", symptoms = "Đau bụng",patient_id = 2, doctor_id = d1.id)
        # db.session.add(m1)
        # db.session.commit()
        #
        # # them thuốc
        # u1 = Unit(name = "mg")
        # u2 = Unit(name = "ml")
        # u3 = Unit(name = "mk")
        # t1 = Type(name = 'Vĩ')
        # t2 = Type(name = "Chai")
        # t3 = Type(name = "Ống")
        # db.session.add_all([u1, u2,u3,t1,t2,t3])
        # db.session.commit()
        #
        # cate1= CategoriesDrug(admin_id = 1)
        # cate2 = CategoriesDrug(admin_id = 1)
        # cate3 = CategoriesDrug(admin_id= 1)
        # db.session.add_all([cate1,cate2,cate3])
        # db.session.commit()
        #
        # dg1 = Drug(drugType = 1, drugUnit =  1, quantity = 50, category_id = 3, name = "Parasitomen", price = "50000") #para
        # dg2 = Drug(drugType=2, drugUnit=2, quantity=30, category_id=3, name = "Thuoc tri khung", price = "100000")
        # dg3 = Drug(drugType=3, drugUnit=3, quantity=50, category_id=3, name = "Thuoc het bug", price = "20000")
        # db.session.add_all([dg1, dg2, dg3])
        # db.session.commit()
        #
        #
        # drugD1 = DrugDetail(medicalDetails = 1, drug = 2, quatity = 2)
        # drugD2 = DrugDetail(medicalDetails = 1, drug = 3, quatity = 3)
        # drugD3 = DrugDetail(medicalDetails=1, drug=4, quatity=1)
        # db.session.add_all([drugD1, drugD2, drugD3])
        # db.session.commit()
        #
# Bảng Unit
#         unit1 = Unit(name='Tablet')
#         unit2 = Unit(name='Syrup')
#         unit3 = Unit(name='Injection')
#         db.session.add_all([unit1, unit2, unit3])
#         db.session.commit()
#         # Bảng Type
#         type1 = Type(name='Antibiotic')
#         type2 = Type(name='Analgesic')
#         type3 = Type(name='Antipyretic')
#         db.session.add_all([type1, type2, type3])
#         db.session.commit()
#
#         # Bảng CategoriesDrug
#         category1 = CategoriesDrug(admin_id=1)  # Giả sử admin_id = 1 tồn tại
#         category2 = CategoriesDrug(admin_id=1)
#         category3 = CategoriesDrug(admin_id=1)
#         db.session.add_all([category1, category2, category3])
#         db.session.commit()
#
#         # Bảng Drug
#         drug1 = Drug(name='Paracetamol', price='5.00', drugType=1, drugUnit=1, quantity=100, category_id=1)
#         drug2 = Drug(name='Amoxicillin', price='10.00', drugType=1, drugUnit=1, quantity=50, category_id=2)
#         drug3 = Drug(name='Ibuprofen', price='7.50', drugType=2, drugUnit=2, quantity=30, category_id=3)
#         db.session.add_all([drug1, drug2, drug3])
#         db.session.commit()

        # Bảng DrugDetail
        drug_detail1 = DrugDetail(medicalDetails_id=1, drug_id=1, medication_instructions='Take after meals', quatity=2)
        drug_detail2 = DrugDetail(medicalDetails_id=1, drug_id=2, medication_instructions='Take before meals', quatity=1)
        drug_detail3 = DrugDetail(medicalDetails_id=2, drug_id=3, medication_instructions='Use as needed', quatity=3)
        db.session.add_all([drug_detail1, drug_detail2, drug_detail3])
        db.session.commit()
        # Thêm tất cả các bản ghi vào session

