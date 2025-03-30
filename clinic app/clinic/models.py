from enum import Enum as UserEnum
from enum import Enum as PaymentMethod
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

class PaymentType(PaymentMethod):
    OFFLINE = 'offline'
    ONLINE = 'online'

class PaymentGateway(PaymentMethod):
    MOMO = 'momo'
    VNPAY = 'vnpay'

class Condition(PaymentMethod):
    PAID = 'paid',
    UNPAID = 'unpaid'

class User(db.Model, UserMixin):
    __tablename__ = 'User'
    __table_args__ = {'extend_existing': True}
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
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, ForeignKey('User.id'),primary_key= True )
    specialization = Column(String(50), nullable=False)
    degree = Column(String(50), nullable=False)
    experience = Column(String(50), nullable=False)
    medicalDetails = relationship('MedicalDetails', backref='doctor', lazy=True)

class Admin(db.Model):
    __tablename__ = 'Admin'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, ForeignKey('User.id'), primary_key=True)

class Patient(db.Model):
    __tablename__ = 'Patient'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, ForeignKey('User.id'), primary_key=True)
    appointments = relationship('Appointment', backref='patient', lazy=True)
    medicalDetails = relationship('MedicalDetails', backref='patient', lazy=True)


class Nurse(db.Model):
    __tablename__ = 'Nurse'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, ForeignKey('User.id'), primary_key=True)
    appointmentLists = relationship('AppointmentList', backref='nurse', lazy=True)
    payments = relationship('Payment', backref='nurse', lazy=True)

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    create_date = Column(DateTime, default=func.now())
    update_date = Column(DateTime, default=func.now(), onupdate=func.now())

class Payment(db.Model):
    __tablename__ = 'Payment'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=datetime.today)
    sum = Column(String(20), nullable=False)
    nurse_id = Column(Integer, ForeignKey('Nurse.id'), nullable=False)
    medicalDetail_id = Column(Integer, ForeignKey('MedicalDetails.id'), nullable=False)
    trangthai = Column(String(20), nullable=True) #thêm

class MedicalDetails(BaseModel):
    __tablename__ = 'MedicalDetails'
    __table_args__ = {'extend_existing': True}
    id =Column(Integer, primary_key=True, autoincrement=True)
    diagnose = Column(String(50), nullable=False)
    symptoms= Column(String(50), nullable=False)
    doctor_id = Column(Integer, ForeignKey('Doctor.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('Patient.id'), nullable=False)
    total = Column(Double, nullable=False)
    payments = relationship('Payment', backref='MedicalDetails', lazy=True)


class OnlinePayment(Payment):
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, ForeignKey('Payment.id'), nullable=False, primary_key=True)
    paymentType = Column(Enum(PaymentGateway), nullable=False)
    idGiaoDich = Column(String(50), nullable=True, unique=True)


class OfflinePayment(Payment):
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, ForeignKey('Payment.id'), nullable=False, primary_key=True)


class AppointmentList(BaseModel):
    __tablename__ = 'AppointmentList'
    __table_args__ = {'extend_existing': True}
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
    __table_args__ = {'extend_existing': True}
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


class Unit(BaseModel):
    __tablename__ = 'Unit'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

    def __str__(self):
        return self.name

class Type(BaseModel):
    __tablename__ = 'Type'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    def __str__(self):
        return self.name

class Drug(BaseModel):
    __tablename__ = 'Drug'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    price = Column(Double, nullable=False)
    drugType = Column(Integer, ForeignKey('Type.id'),nullable=False)
    drugUnit = Column(Integer,ForeignKey('Unit.id'), nullable=False)
    quantity = Column(Integer, nullable=False)


class DrugDetail(BaseModel):
    __tablename__ = 'DrugDetail'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    medicalDetails = Column(Integer, ForeignKey('MedicalDetails.id') , nullable=False)
    drug = Column(Integer,ForeignKey('Drug.id'), nullable=False)
    quantity = Column( Integer, nullable=False)
    description = Column(String(255),nullable=False)



if __name__ == '__main__':
    with app.app_context():
        pass
        # db.create_all()  # Tạo các bảng trong cơ sở dữ liệu
        # db.session.commit()
        #
        # # #Existing admin, patient, nurse entries
        # admin1 = User(
        #     name='admin1',
        #     username='admin1',
        #     password=str(utils.hash_password("123")),  # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='2251010077phuong@ou.edu.vn',
        #     user_role=UserRole.ADMIN,
        #     gender=Gender.FEMALE,
        #     phone='0123456',
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
        #     password=str(utils.hash_password("123")),  # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='2251010062mai@ou.edu.vn',
        #     user_role=UserRole.PATIENT,
        #     gender=Gender.MALE,
        #     phone='0962395651',
        #     dob=date(2004, 3, 10)
        # )
        # db.session.add(patient1)
        # db.session.commit()
        # patient_entry1 = Patient(id=patient1.id)
        # db.session.add(patient_entry1)
        #
        # patient2 = User(
        #     name='patient2',
        #     username='patient2',
        #     password=str(utils.hash_password("123")), # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='nglhongphuong@gmail.com',
        #     user_role=UserRole.PATIENT,
        #     gender=Gender.FEMALE,
        #     phone='0708504288',
        #     dob=date(2004, 7, 23)
        # )
        # db.session.add(patient2)
        # db.session.commit()
        # patient_entry2 = Patient(id=patient2.id)
        # db.session.add(patient_entry2)
        #
        # patient3 = User(
        #     name='patient3',
        #     username='patient3',
        #     password=str(utils.hash_password("123")), # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='2251010006bao@ou.edu.vn',
        #     user_role=UserRole.PATIENT,
        #     gender=Gender.MALE,
        #     phone='0944180364',
        #     dob=date(2004, 3, 10)
        # )
        # db.session.add(patient3)
        # db.session.commit()
        # patient_entry3 = Patient(id=patient3.id)
        # db.session.add(patient_entry3)
        #
        # nurse1 = User(
        #     name='nurse1',
        #     username='nurse1',
        #     password=str(utils.hash_password("123")),  # Mật khẩu được băm
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
        # nurse2 = User(
        #     name='y ta 2',
        #     username='nurse2',
        #     password=str(utils.hash_password("123")),  # Mật khẩu được băm
        #     avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
        #     email='hhhhh@gmail.com',
        #     user_role=UserRole.NURSE,
        #     gender=Gender.FEMALE,
        #     phone='123455567788',
        #     dob=date(2004, 3, 10)
        # )
        # db.session.add(nurse2)
        # db.session.commit()
        # nurse_entry1 = Nurse(id=nurse2.id)
        # db.session.add(nurse_entry1)
        # db.session.commit()
        #
        #  #Create appointment lists
        # appointment_list1 = AppointmentList(schedule_date=date(2024, 12, 5), nurse_id=5)
        # appointment_list2 = AppointmentList(schedule_date=date(2024, 12, 6), nurse_id=6)
        # db.session.add(appointment_list1)
        # db.session.add(appointment_list2)
        # db.session.commit()
        #
        # #Add appointments to the lists
        # appointment1 = Appointment(
        #     description="Tái khám",
        #     schedule_date=date(2024, 11, 5),
        #     schedule_time=datetime.strptime("08:00", "%H:%M").time(),
        #     patient_id= 2,
        #     appointment_list_id=1
        # )
        # db.session.add(appointment1)
        # db.session.commit()
        # appointment2 = Appointment(
        #     description="Đau răng",
        #     schedule_date=date(2024, 12, 5),
        #     schedule_time=datetime.strptime("09:00", "%H:%M").time(),
        #     patient_id=3,
        #     appointment_list_id=1
        # )
        # appointment3 = Appointment(
        #     description="Bị sốt 3 ngày, khó tiêu có triệu chứng ói khuya",
        #     schedule_date=date(2024, 12, 6),
        #     schedule_time=datetime.strptime("10:00", "%H:%M").time(),
        #     patient_id=4,
        #     appointment_list_id=2
        # )
        # appointment4 = Appointment(
        #     description="Tái khám",
        #     schedule_date=date(2024, 2, 6),
        #     schedule_time=datetime.strptime("11:00", "%H:%M").time(),
        #     patient_id=2,
        #     appointment_list_id=2
        # )
        #
        # db.session.add(appointment1)
        # db.session.add(appointment2)
        # db.session.add(appointment3)
        # db.session.add(appointment4)
        # db.session.commit()
        #
        # n3 = User(name='Ha Vi', username='nurse3', password=str(utils.hash_password('1234')), phone="01234567",
        #           gender=Gender.FEMALE,
        #           address='123 HVC, TPHCM', user_role=UserRole.NURSE, email="2251093n1@gmail.com",
        #           dob=date(2004, 12, 7))
        # n4 = User(name='Thi Huong', username='nurse4', password=str(utils.hash_password('1234')), phone="01234423567",
        #           gender=Gender.FEMALE,
        #           address='12 PVD, TPHCM', user_role=UserRole.NURSE, email="2251093n2@gmail.com",
        #           dob=date(2004, 12, 7))
        # n5 = User(name='Minh Tuyet', username='nurse5', password=str(utils.hash_password('1234')),
        #           phone="012756734567",
        #           gender=Gender.FEMALE,
        #           address='13 NT, TPHCM', user_role=UserRole.NURSE, email="2251093n3@gmail.com",
        #           dob=date(2004, 12, 7))
        # n6 = User(name='Thanh Tung', username='nurse6', password=str(utils.hash_password('1234')),
        #           phone="01234509767",
        #           gender=Gender.MALE,
        #           address='3 ADL, TPHCM', user_role=UserRole.NURSE, email="2251093n4@gmail.com",
        #           dob=date(2004, 12, 7))
        #
        # db.session.add_all([n3, n4, n5, n6])
        # db.session.commit()
        # nurse3 = Nurse(id = n3.id)
        # nurse4 = Nurse(id = n4.id)
        # nurse5 = Nurse(id = n5.id)
        # nurse6 = Nurse(id = n6.id)
        #
        # db.session.add(nurse3)
        # db.session.add(nurse4)
        # db.session.add(nurse5)
        # db.session.add(nurse6)
        # db.session.commit()
        #
        # d1 = User(name='Thanh Hien', username='doctor1', password=str(utils.hash_password('1234')),
        #           phone="0123509767",
        #           gender=Gender.FEMALE,
        #           address='3 PH, TPHCM', user_role=UserRole.DOCTOR, email="225109d1@gmail.com",
        #           dob=date(2004, 1, 7))
        # db.session.add(d1)
        # db.session.commit()
        # doctor1 = Doctor(id = d1.id, specialization = "Nội soi",degree = "Chuyên khoa I", experience = "6")
        # db.session.add(doctor1)
        # db.session.commit()
        #
        # # them thuốc
        # u1 = Unit(name = "vỉ")
        # u2 = Unit(name = "viên")
        # u3 = Unit(name = "chai")
        # t1 = Type(name = 'Vitamin')
        # t2 = Type(name = "Kháng Sinh")
        # t3 = Type(name = "Giảm đau")
        # db.session.add_all([u1,u2,u3,t1,t2,t3])
        # db.session.commit()
        # drug1 = Drug(name="paradol", drugUnit=u1.id, drugType=u2.id, price=200, quantity=100)
        # db.session.add(drug1)
        # db.session.commit()
        #
        # drug1 = Drug(name="Paradol", price=2000, drugType=t1.id, drugUnit=u1.id, quantity=500)
        # drug2 = Drug(name="Cefixime", price=3000, drugType=t2.id, drugUnit=u2.id, quantity=300)
        # drug3 = Drug(name="Vitamin C", price=1000, drugType=t3.id, drugUnit=u3.id, quantity=100)
        #
        # db.session.add_all([drug1, drug2, drug3])
        # db.session.commit()
        #
        #
        # medical1 = MedicalDetails(diagnose="Sốt", symptoms="Ho, sốt cao", doctor_id=d1.id, patient_id=2, total=300000)
        # medical2 = MedicalDetails(diagnose="Viêm họng", symptoms="Đau họng, khó nuốt", doctor_id=d1.id, patient_id=4,
        #                           total=150000)
        # medical3 = MedicalDetails(diagnose="Mệt mỏi", symptoms="Đau nhức cơ thể", doctor_id=d1.id, patient_id=4,
        #                           total=200000)
        #
        # db.session.add_all([medical1, medical2, medical3])
        # db.session.commit()
        # db.session.add(medical2)
        # db.session.commit()
        #
        # detail1 = DrugDetail(medicalDetails=medical1.id, drug=drug1.id, quantity=10, description='Ăn trước khi uống')
        # detail2 = DrugDetail(medicalDetails=medical1.id, drug=drug2.id, quantity=5, description='Sáng và chiều')
        # detail3 = DrugDetail(medicalDetails=medical2.id, drug=drug3.id, quantity=20,description='Chỉ uống khi sốt trên 38 độn')
        # detail4 = DrugDetail(medicalDetails=medical2.id, drug=drug1.id, quantity=15, description='Uống khi khó tiêu')
        # detail5 = DrugDetail(medicalDetails=medical1.id, drug=drug2.id, quantity=8, description='Uống khi hạ đường huyết')
        #
        # db.session.add_all([detail1, detail2, detail3, detail4, detail5])
        # db.session.commit()
        #
