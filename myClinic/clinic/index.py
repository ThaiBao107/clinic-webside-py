# from crypt import methods
# from crypt import methods
# from crypt import methods
from calendar import c
#from crypt import methods

from sqlalchemy import Double
#from crypt import methods

from sqlalchemy.testing.plugin.plugin_base import config

from clinic import app, utils, login, mail, dao
from flask_login import login_user, logout_user, login_required
from flask import render_template, request, url_for, redirect, flash, jsonify, session
import cloudinary.uploader

#from clinic.dao import get_medicaldetails, create_payment
from clinic.models import Condition,UserRole, Gender, User, Patient, Nurse, Appointment, OfflinePayment, OnlinePayment
from clinic.forms import ResetPasswordForm, ChangePasswordForm
from flask_mail import Message
from clinic import settings
from clinic.decorators import nursesnotloggedin
from datetime import datetime
from clinic import app, db, utils
from clinic import vnpay
import pickle

from clinic.vnpay import VNpay


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("index.html")
@app.route('/register', methods=['get', 'post'])
def user_register():
    err_msg = ""

    if request.method.__eq__('POST'):
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        confirm = request.form.get('confirm')
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        address = request.form.get('address')
        avatar_path = None
        gender = None
        if request.form.get('gender') == 'male':
            gender = Gender.MALE
        else:
            gender = Gender.FEMALE
        try:
            if password.strip().__eq__(confirm.strip()):
                avatar = request.files.get('avatar')
                if avatar:
                    res = cloudinary.uploader.upload(avatar)
                    avatar_path = res['secure_url']
                # kiểm tra mật khẩu xác thực
                dao.add_user(name=name, username=username,
                             password=password, email=email, avatar=avatar_path,
                             gender=gender, dob=dob, phone=phone, address=address)
                return redirect(url_for('user_login'))
            else:
                err_msg = "Mật khẩu không khớp !!"
        except Exception as ex:
            err_msg = "Hệ thống đang lỗi" + str(ex)

    return render_template("auth/register.html", err_msg=err_msg)


@app.route('/login', methods=['get', 'post'])
def user_login():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.check_login(username=username, password=password)
        if user:
            # Ghi nhan trang thai dang nhap user qua flask_login import login_user
            login_user(user=user)
            return redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác!', 'warning')

    return render_template("auth/login.html")


@app.route('/admin-login', methods=['post'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = dao.check_login(username=username,
                           password=password,
                           role=UserRole.ADMIN)
    if user:
        # Ghi nhan trang thai dang nhap user qua flask_login import login_user
        login_user(user=user)
    return redirect('/admin')


@login.user_loader
def user_load(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/signout', methods=['get', 'post'])
def user_signout():
    logout_user()
    return redirect(url_for('user_login'))


def send_email(user):
    token = user.get_token()
    msg = Message('Password Reset Request', recipients=[user.email], sender='phongkhamsaigoncare@gmail.com')
    msg.body = f''' Để reset lại password. Hãy theo dõi đường link phía dưới.
    {url_for('reset_token', token=token, _external=True)}
    
    Nếu bạn chưa từng gửi yêu cầu thay đổi password. Làm ơn bỏ qua lời nhắn này.

    '''
    mail.send(msg)
    return None


@app.route('/reset_password', methods=['get', 'post'])
def reset_password():
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip()).first()
        if user:
            send_email(user)
            flash('Yêu cầu đã được gửi. Hãy kiểm tra emmail của bạn', 'success')
            return redirect(url_for('user_login'))
        else:
            flash('Không tìm thấy người dùng', 'Warning')
    return render_template("auth/reset_password.html",
                           title='Reset Password', form=form, legend="Reset Password")


@app.route('/change_password/<token>', methods=['get', 'post'])
def reset_token(token):
    user = User.verify_token(token)

    if user is None:
        flash('That is invalid token. Please try again', 'warning')
        return redirect(url_for('reset_password'))  # chuyển về trang chủ nhập lại mail nếu không thấy người dùng!
    form = ChangePasswordForm()
    if form.validate_on_submit():
        hashed_password = utils.hash_password(form.password.data.strip())
        user.password = hashed_password
        db.session.commit()
        flash('Password đã thay đổi!', 'Success')
        return redirect(url_for('user_login'))
    if form.errors:
        print(form.errors)

    return render_template('auth/change_password.html', legend='Change Password',
                           title='Change Password', form=form, token=token)


@app.route('/profile')
def profile():
    return render_template('profile/profile.html')


# Chưa làm edit profile


# Lịch khám
@app.route('/appointment')
@login_required
def appointment():
    if current_user.user_role.value == 'patient':
        patient = Patient.query.filter_by(id=current_user.id).first()  # Get the patient by current_user's id
        if patient:
            return render_template('patient/appointment.html', appointments=patient.appointments,
                                   patient=patient)
    return redirect(url_for('index'))


@app.route('/api/delete-appointment/<appointment_id>', methods=['delete'])
def delete_appointment(appointment_id):
    try:
        appoint = Appointment.query.get(appointment_id)
        if not appoint:
            return jsonify({'message': 'Appointment not found'}), 404

        db.session.delete(appoint)
        db.session.commit()
        return jsonify({'message': f'Appointment {appointment_id} deleted successfully'}), 200
    except Exception as ex:
        db.session.rollback()  # Rollback in case of error

    return jsonify({'message': f'Error occurred: {str(ex)}'}), 500


@app.route('/register_appointment')
def register_appointment():
    return render_template('appointment/register_appointment.html')


@app.route('/payment', methods=['get', 'post'])
# @nursesnotloggedin
def payment():
    mes = ""
    info = None
    total = 0
    if request.method.__eq__('POST'):
        medical_id = request.form.get('k')
        print("TMP")
        total_payment = dao.payment_total(medical_id)

        print(total_payment)
        total_medical = dao.get_medicaldetails(medical_id)
        tiendu = int(utils.total(medical_id)) - total_payment
        if dao.get_medicaldetails(medical_id) and (tiendu > 0):
            drug_list = None
            m = dao.get_medicaldetails(medical_id)

            u = dao.get_user(m.patient_id)

            if m:
                info = dao.get_info(m.patient_id)
                drug_list = dao.get_drugDetail(medical_id)
                print("haha")
                print(medical_id)
                print(info)
                print(drug_list)
                user_doctor = None
                if m and info and drug_list:
                    if u.user_role.value == 'patient':
                        user_doctor = dao.get_user(info[1].id)
                else:
                    mes = "Khong tim thay thong tin"
                return render_template('payment/payment.html', user=u, info=info, drug_list=drug_list,
                                           doctor=user_doctor,tiendu = tiendu, mes = mes)
        else:
                mes = "Khong tim thay thong tin"
    return render_template('payment/payment.html', mes=mes)





@app.route('/payment_return_vnpay', methods=['GET','POST'])
# @nursesnotloggedin
def payment_return():
    inputData = request.args
    vnp = VNpay()
    vnp.responseData = inputData.to_dict()
    vnp_ResponseCode = inputData["vnp_ResponseCode"]
    vnp_Amount = int(inputData["vnp_Amount"])
    # trans_code = inputData["vnp_BankTranNo"]
    # date1 = inputData["vnp_CreateDate"]
    transtraction_id = inputData["vnp_TransactionNo"]
    print(transtraction_id)
    print(inputData)
    print(155555)
    # Kiểm tra tính toàn vẹn của dữ liệu
    if vnp_ResponseCode == "00":
        # Lấy thông tin lịch hẹn từ request và thông tin người dùng hiện tại
            payment_id = int(inputData["vnp_TxnRef"]) - 1000
            print(payment_id)
            p = dao.get_only_payment(payment_id)
            print(p)
            if p:
                p.trangthai = "Condition.PAID"
                db.session.commit()
                p.idGiaoDich = transtraction_id
                # p.idGiaoDich = str(transtraction_id)
                print("p.idGiaoDich")

                db.session.commit()
                print(p.idGiaoDich)
            print("Thanh toán thành công!")
            return redirect('/return_API')

    else:
        # Xử lý trường hợp lỗi từ VNPAY
        print("Loi")
        return redirect('/')



@app.route('/return_API', methods=['GET'])
def return_API():
    return render_template('payment/returnAPI.html')


@app.route('/api/bills', methods=['GET', 'POST'])
def create_bill():
    if request.method.__eq__('POST'):
        data = request.get_json()
        id = data.get('user_id')
        type = data.get('type_payment')
        tientra = data.get('tien_tra')
        print(tientra)
        #neu thanh toan online
        print(id)
        print(type)
        tientra_off = ""
        info = dao.get_info(id)
        # print(info)
        if type == "radio_offline":
            tientra_off = utils.total(info[0].id)
            print(tientra_off)

        p = None
        if type == "radio_offline":
            print(1)
            p = dao.add_payment(date = datetime.now(), sum = tientra_off, nurse_id =8, medical_id = info[0].id,
                                idGiaoDich = None, loai = type)  #fix lai xem sao de lam cho y ta dung
        else:
            print(2)
            p =dao.add_payment(date=datetime.now(), sum=tientra, nurse_id=8, medical_id=info[0].id,
                                idGiaoDich=None, loai=type)  # fix lai xem sao de lam cho y ta dung
        db.session.add(p)
        db.session.commit()
        print("Xong ")
    return render_template('index.html')



@app.route('/paymentlist', methods=['GET', 'POST'])
def paymentlist():
    mess = ""
    id = current_user.id
    info = dao.get_info(id)
    print("paymentlist")
    print(info)
    payment = dao.get_payment(medical_id=info[0].id)
    print(payment)
    list = []
    if payment:
        for p in payment:
            if p[1].trangthai.__eq__("Condition.UNPAID"):
                list.append(p)
        print(list)
        if len(list) == 0:
            list = None
            mess = "Chưa có hóa đơn"
    else:
        list = None
        mess = "Không có thông tin"
    return render_template('payment/paymentlist.html', payment = list, mess=mess)



@app.route('/info_payment', methods=['GET', 'POST'])
def info_payment():
    print("info payment")
    if request.method.__eq__('POST'):
        print("Da do")
        payment_id = request.form.get("payment_id")
        print(payment_id)
        id = current_user.id
        info = dao.get_info(id)
        print(info[0].id)
        drug_list = dao.get_drugDetail(info[0].id)
        p = dao.get_only_payment(payment_id)
        print(1)
        print(drug_list)
        print(info)
        return render_template('payment/info.html', info=info, drug_list = drug_list, tiendu = p.sum)




@app.route('/api/process_vnpay', methods=['POST'])
def process_vnpay():
    total = None

    if request.method.__eq__('POST'):
        print("Do")
        data = request.get_json()
        total = data.get('total')
    print("process VN")
    patient_id = current_user.id
    info = dao.get_info(patient_id)
    # print(patient_id)
    # print(medicaldetails.id)
    print(info)
    print("VNPAY")
    print(total)

    if request.method == 'POST':
        # Process input data from form
        order_type = "billpayment"
        order_desc = f"Thanh toán hoá đơn cho bệnh nhân {patient_id}, với số tiền {total} VND"

        # Build URL Payment
        vnp = VNpay()
        vnp.requestData['vnp_Version'] = '2.1.0'
        vnp.requestData['vnp_Command'] = 'pay'
        vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
        vnp.requestData['vnp_OrderInfo'] = order_desc
        vnp.requestData['vnp_OrderType'] = order_type
        # Check language, default: vn

        vnp.requestData['vnp_Locale'] = 'vn'
        ipaddr = request.remote_addr
        # Build URL Payment
        vnp = VNpay()
        vnp.requestData['vnp_Amount'] = int(total) * 100
        vnp.requestData['vnp_CurrCode'] = 'VND'
        print("Medical process ")
        print("medical details:")
        print(info[0].id)
        k = dao.get_Payment2(medical_id=info[0].id)
        print("K: ")
        print(k)
        vnp.requestData['vnp_TxnRef'] =  k + 1000


        vnp.requestData['vnp_OrderInfo'] = order_desc
        vnp.requestData['vnp_OrderType'] = order_type
        vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
        vnp.requestData['vnp_IpAddr'] = ipaddr
        vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL

        vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET_KEY)
        print(f"Redirecting to VNPAY: {vnpay_payment_url}")
        # Redirect to VNPAY Payment URL
        return redirect(vnpay_payment_url)
    else:
        return render_template('payment/payment.html', title="Thanh toán")



if __name__ == "__main__":
    # nạp trang admin
    from clinic.admin import *

    app.run(debug=True)
