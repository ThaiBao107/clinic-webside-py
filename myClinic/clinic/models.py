from enum import Enum as UserEnum
from enum import Enum as PaymentOnline
from enum import Enum as DrugType
from enum import Enum as DrugUnit


from mypy.types import names
from sqlalchemy import DateTime, Enum, Column, Integer, String, Float, Boolean, ForeignKey, Date, func, Time, Double
from sqlalchemy.orm import relationship
from clinic import app, db, dao
from  datetime import datetime, date
from flask_login import UserMixin
from itsdangerous.url_safe import URLSafeSerializer as Serializer


class UserRole(UserEnum):
    ADMIN = 'admin'
    PATIENT = 'patient'
    NURSE = 'nurse'


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
    phone = Column(String(50), nullable=False)
    gender = Column(Enum(Gender))
    address = Column(String(255), default='HoChiMinh')
    dob = Column(Date, default=date.today)


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


# class Phone(db.Model):
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     value = Column(String(50), unique=True, nullable=False)
#     user_id = Column(Integer, ForeignKey(User.id), nullable=False)


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
    medicalDetails = relationship('MedicalDetails', backref='Payment', lazy=True)


class MedicalDetails(db.Model):
    __tablename__ = 'MedicalDetails'
    id =Column(Integer, primary_key=True, autoincrement=True)
    diagnose = Column(String(50), nullable=False)
    symptoms= Column(String(50), nullable=False)
    doctor_id = Column(Integer, ForeignKey('Doctor.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('Patient.id'), nullable=False)
    payment_id = Column(Integer, ForeignKey('Payment.id'), nullable=False)


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
    medicalDetails = Column(Integer, ForeignKey('MedicalDetails.id') , nullable=False)
    drug = Column(Integer,ForeignKey('Drug.id'), nullable=False)
    quatity = Column( Double, nullable=False)




if __name__ == '__main__':
    with app.app_context():
        #db.create_all()  # Tạo các bảng trong cơ sở dữ liệu
        # db.session.commit()

        # Existing admin, patient, nurse entries
        # admin1 = User(
        #     name='admin1',
        #     username='admin1',
        #     password=str(dao.hash_password("123")),  # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='2251010077phuong@ou.edu.vn',
        #     user_role=UserRole.ADMIN,
        #     gender=Gender.FEMALE,
        #     phone='0708602388',
        #     dob=date(2004, 7, 23)
        # )
        # db.session.add(admin1)
        # db.session.commit()
        # admin_entry = Admin(id=admin1.id)
        # db.session.add(admin_entry)
        #
        # patient1 = User(
        #     name='patient1',
        #     username='patient1',
        #     password=str(dao.hash_password("123")),  # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='2251010062mai@ou.edu.vn',
        #     user_role=UserRole.PATIENT,
        #     gender=Gender.MALE,
        #     phone='0908703277',
        #     dob=date(2004, 7, 10)
        # )
        # db.session.add(patient1)
        # db.session.commit()
        # patient_entry1 = Patient(id=patient1.id)
        # db.session.add(patient_entry1)
        #
        # patient2 = User(
        #     name='patient2',
        #     username='patient2',
        #     password=str(dao.hash_password("123")), # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='nglhongphuong@gmail.com',
        #     user_role=UserRole.PATIENT,
        #     gender=Gender.FEMALE,
        #     phone='0703792627',
        #     dob=date(2004, 3, 10)
        # )
        # db.session.add(patient2)
        # db.session.commit()
        # patient_entry2 = Patient(id=patient2.id)
        # db.session.add(patient_entry2)
        #
        # nurse1 = User(
        #     name='nurse1',
        #     username='nurse2',
        #     password=str(dao.hash_password("123")),  # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='nguyenluhongphuong@gmail.com',
        #     user_role=UserRole.NURSE,
        #     gender=Gender.FEMALE,
        #     phone='0703792690',
        #     dob=date(2004, 3, 10)
        # )
        # db.session.add(nurse1)
        # db.session.commit()
        # nurse_entry1 = Nurse(id=nurse1.id)
        # db.session.add(nurse_entry1)
        # db.session.commit()
        #
        # # Create appointment lists
        # appointment_list1 = AppointmentList(schedule_date=date(2024, 12, 5), nurse_id=nurse1.id)
        # appointment_list2 = AppointmentList(schedule_date=date(2024, 12, 6), nurse_id=nurse1.id)
        # db.session.add(appointment_list1)
        # db.session.add(appointment_list2)
        # db.session.commit()
        #
        # # Add appointments to the lists
        # appointment1 = Appointment(
        #     description="Tái khám",
        #     schedule_date=date(2024, 12, 5),
        #     schedule_time=datetime.strptime("08:00", "%H:%M").time(),
        #     patient_id=patient1.id,
        #     appointment_list_id=appointment_list1.id
        # )
        # appointment2 = Appointment(
        #     description="Đau răng",
        #     schedule_date=date(2024, 12, 5),
        #     schedule_time=datetime.strptime("09:00", "%H:%M").time(),
        #     patient_id=patient2.id,
        #     appointment_list_id=appointment_list1.id
        # )
        # appointment3 = Appointment(
        #     description="Bị sốt 3 ngày, khó tiêu có triệu chứng ói khuya",
        #     schedule_date=date(2024, 12, 6),
        #     schedule_time=datetime.strptime("10:00", "%H:%M").time(),
        #     patient_id=patient1.id,
        #     appointment_list_id=appointment_list2.id
        # )
        # appointment4 = Appointment(
        #     description="Tái khám",
        #     schedule_date=date(2024, 12, 6),
        #     schedule_time=datetime.strptime("11:00", "%H:%M").time(),
        #     patient_id=patient2.id,
        #     appointment_list_id=appointment_list2.id
        # )
        #
        # db.session.add(appointment1)
        # db.session.add(appointment2)
        # db.session.add(appointment3)
        # db.session.add(appointment4)
        # db.session.commit()

        n1 = User(name='Ha Vi', username='nurse1', password=str(dao.hash_password('1234')), phone="01234567",
                  gender=Gender.FEMALE,
                  address='123 HVC, TPHCM', user_role=UserRole.NURSE, email="2251093n1@gmail.com",
                  dob=date(2004, 12, 7))
        n2 = User(name='Thi Huong', username='nurse5', password=str(dao.hash_password('1234')), phone="01234423567",
                  gender=Gender.FEMALE,
                  address='12 PVD, TPHCM', user_role=UserRole.NURSE, email="2251093n2@gmail.com",
                  dob=date(2004, 12, 7))
        n3 = User(name='Minh Tuyet', username='nurse3', password=str(dao.hash_password('1234')),
                  phone="012756734567",
                  gender=Gender.FEMALE,
                  address='13 NT, TPHCM', user_role=UserRole.NURSE, email="2251093n3@gmail.com",
                  dob=date(2004, 12, 7))
        n4 = User(name='Thanh Tung', username='nurse4', password=str(dao.hash_password('1234')),
                  phone="01234509767",
                  gender=Gender.MALE,
                  address='3 ADL, TPHCM', user_role=UserRole.NURSE, email="2251093n4@gmail.com",
                  dob=date(2004, 12, 7))

        # db.session.add_all([n1, n2, n3, n4])
        nurse1 = Nurse(id = 11)
        nurse2 = Nurse(id = 12)
        nurse3 = Nurse(id = 13)
        nurse4 = Nurse(id = 14)

        db.session.add(nurse1)
        db.session.add(nurse2)
        db.session.add(nurse3)
        db.session.add(nurse4)
        db.session.commit()


