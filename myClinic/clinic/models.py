from enum import Enum as UserEnum
from sqlalchemy import DateTime, Enum, Column, Integer, String, Float, Boolean, ForeignKey, Date, func, Time
from sqlalchemy.orm import relationship
from clinic import app, db, dao
from datetime import datetime, date
from flask_login import UserMixin
from itsdangerous.url_safe import URLSafeSerializer as Serializer


class UserRole(UserEnum):
    ADMIN = 'admin'
    PATIENT = 'patient'
    NURSE = 'nurse'


class Gender(UserEnum):
    MALE = 'male'
    FEMALE = 'female'

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(70), nullable=False)
    avatar = Column(String(255))
    email = Column(String(50))
    user_role = Column(Enum(UserRole), nullable=False)
    gender = Column(Enum(Gender))
    phone = Column(String(20), nullable=True)
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

class Admin(db.Model):
    id = Column(Integer, ForeignKey(User.id), primary_key=True)

class Patient(db.Model):
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    appointments = relationship('Appointment', backref='patient', lazy=True)

class Nurse(db.Model):
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    appointmentLists = relationship('AppointmentList', backref='nurse', lazy=True)

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    create_date = Column(DateTime, default=func.now())
    update_date = Column(DateTime, default=func.now(), onupdate=func.now())

class AppointmentList(BaseModel):
    schedule_date = Column(Date, unique=True)
    nurse_id = Column(Integer, ForeignKey(Nurse.id), nullable=False)
    appointments = relationship('Appointment', backref='appointment_list', lazy=True)

class Status(UserEnum):
    PENDING = 'pending' #Chờ xác nhận
    CONFIRMED = 'confirmed' #đã xác nhận
    CANCELED = 'canceled' # bị hủy
    COMPLETED = 'completed'  # Đã khám bệnh - bác sĩ tự xác nhận

class Appointment(BaseModel):
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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tạo các bảng trong cơ sở dữ liệu
        db.session.commit()

        # Existing admin, patient, nurse entries
        admin1 = User(
            name='admin1',
            username='admin1',
            password=str(dao.hash_password("123")),  # Mật khẩu được băm
            avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
            email='2251010077phuong@ou.edu.vn',
            user_role=UserRole.ADMIN,
            gender=Gender.FEMALE,
            phone='0708602388',
            dob=date(2004, 7, 23)
        )
        db.session.add(admin1)
        db.session.commit()
        admin_entry = Admin(id=admin1.id)
        db.session.add(admin_entry)

        patient1 = User(
            name='patient1',
            username='patient1',
            password=str(dao.hash_password("123")),  # Mật khẩu được băm
            avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
            email='2251010062mai@ou.edu.vn',
            user_role=UserRole.PATIENT,
            gender=Gender.MALE,
            phone='0908703277',
            dob=date(2004, 7, 10)
        )
        db.session.add(patient1)
        db.session.commit()
        patient_entry1 = Patient(id=patient1.id)
        db.session.add(patient_entry1)

        patient2 = User(
            name='patient2',
            username='patient2',
            password=str(dao.hash_password("123")), # Mật khẩu được băm
            avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
            email='nglhongphuong@gmail.com',
            user_role=UserRole.PATIENT,
            gender=Gender.FEMALE,
            phone='0703792627',
            dob=date(2004, 3, 10)
        )
        db.session.add(patient2)
        db.session.commit()
        patient_entry2 = Patient(id=patient2.id)
        db.session.add(patient_entry2)

        nurse1 = User(
            name='nurse1',
            username='nurse2',
            password=str(dao.hash_password("123")),  # Mật khẩu được băm
            avatar='https://res.cloudinary.com/dmz9kuzue/image/upload/v1732014605/samples/dessert-on-a-plate.jpg',
            email='nguyenluhongphuong@gmail.com',
            user_role=UserRole.NURSE,
            gender=Gender.FEMALE,
            phone='0703792690',
            dob=date(2004, 3, 10)
        )
        db.session.add(nurse1)
        db.session.commit()
        nurse_entry1 = Nurse(id=nurse1.id)
        db.session.add(nurse_entry1)
        db.session.commit()

        # Create appointment lists
        appointment_list1 = AppointmentList(schedule_date=date(2024, 12, 5), nurse_id=nurse1.id)
        appointment_list2 = AppointmentList(schedule_date=date(2024, 12, 6), nurse_id=nurse1.id)
        db.session.add(appointment_list1)
        db.session.add(appointment_list2)
        db.session.commit()

        # Add appointments to the lists
        appointment1 = Appointment(
            description="Tái khám",
            schedule_date=date(2024, 12, 5),
            schedule_time=datetime.strptime("08:00", "%H:%M").time(),
            patient_id=patient1.id,
            appointment_list_id=appointment_list1.id
        )
        appointment2 = Appointment(
            description="Đau răng",
            schedule_date=date(2024, 12, 5),
            schedule_time=datetime.strptime("09:00", "%H:%M").time(),
            patient_id=patient2.id,
            appointment_list_id=appointment_list1.id
        )
        appointment3 = Appointment(
            description="Bị sốt 3 ngày, khó tiêu có triệu chứng ói khuya",
            schedule_date=date(2024, 12, 6),
            schedule_time=datetime.strptime("10:00", "%H:%M").time(),
            patient_id=patient1.id,
            appointment_list_id=appointment_list2.id
        )
        appointment4 = Appointment(
            description="Tái khám",
            schedule_date=date(2024, 12, 6),
            schedule_time=datetime.strptime("11:00", "%H:%M").time(),
            patient_id=patient2.id,
            appointment_list_id=appointment_list2.id
        )

        db.session.add(appointment1)
        db.session.add(appointment2)
        db.session.add(appointment3)
        db.session.add(appointment4)
        db.session.commit()


