from datetime import datetime, timedelta
from clinic import app, login, mail, dao, utils
from flask_login import login_user, logout_user, login_required
from flask import render_template, request, url_for, redirect, flash, jsonify, session, make_response, abort
import cloudinary.uploader
from clinic.models import Gender, Patient, Appointment, AppointmentList, Status, Doctor, DrugDetail, MedicalDetails
from clinic.forms import ResetPasswordForm, ChangePasswordForm
from flask_mail import Message
import openpyxl
from io import BytesIO
from clinic import vnpay, settings
from sqlalchemy import Row
from clinic import db


@app.route("/")
def index():
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
    if 'drug_list' in session:
        del session['drug_list']
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
    doctor = None
    if current_user.user_role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(id=current_user.id).first()
    return render_template('profile/profile.html', doctor=doctor)


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


@app.route('/search_patient', methods=['get', 'post'])
def search_patient():
    if request.method.__eq__('POST'):
        if current_user.user_role.value == 'nurse':
            patient_id = request.form.get('patient_id')
            if not Patient.query.filter_by(id=patient_id).first():
                flash('Không tìm thấy bệnh nhân!', 'warning')
                return render_template('appointment/search_patient.html')
            else:
                patient_info = User.query.filter_by(id=patient_id).first()
                return redirect(url_for('register_appointment',
                                        patient_id=patient_id,
                                        patient_info=patient_info))
    return render_template('appointment/search_patient.html')


@app.route('/register_appointment', methods=['GET', 'POST'])
def register_appointment():
    patient_id = request.args.get('patient_id')  # Lấy ID từ URL nếu có
    appointment_details = None
    patient_info = User.query.filter_by(id=patient_id).first()
    if current_user.user_role.value == 'patient':
        patient_info = current_user
        patient_id = patient_info.id
    if request.method.__eq__('POST'):
        patient_id = request.form['patient_id']
        if not patient_info:
            patient_info = User.query.filter_by(id=patient_id).first()
        description = request.form.get('description')
        schedule_date = request.form.get('schedule_date')
        schedule_time = request.form.get('schedule_time')
        if description and schedule_date and schedule_time:
            if dao.existing_appointment(schedule_date, schedule_time):
                flash("Lịch khám đã được đăng ký rồi!", 'warning')
            elif dao.check_max_patients_for_a_day(schedule_date):
                flash('Lịch khám đã đặt giới hạn đăng ký! ', 'warning')
            else:
                dao.add_appointment(
                    description=description,
                    schedule_date=schedule_date,
                    schedule_time=schedule_time,
                    patient_id=patient_id
                )
                flash('Đăng ký lịch khám thành công!', 'success')
                appoint = Appointment.query.filter_by(patient_id=patient_id, schedule_date=schedule_date,
                                                      schedule_time=schedule_time).first()
                appointment_details = {
                    'id': appoint.id,
                    'patient_id': patient_id,
                    'description': description,
                    'schedule_date': schedule_date,
                    'schedule_time': schedule_time
                }

    return render_template('appointment/register_appointment.html', appointment_details=appointment_details,
                           patient_info=patient_info, patient_id=patient_id)


# xử lý về y tá
@app.route('/list_appointment', methods=['GET', 'POST'])
@login_required
# bổ sung login dưới dạng y tá nữa vì rất có thể nếu đăng nhập là nguời khác thì vẫn truy cập được
def list_appointment():
    selected_date = request.args.get('schedule_date')  # Lấy ngày từ form
    appointments = []
    appointment_list = []
    formatted_date = None

    if selected_date:
        formatted_date = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%d-%m-%Y')

        # Truy vấn danh sách bệnh nhân cho ngày đã chọn
        appointments = (
            db.session.query(Appointment, User)
            .join(User, Appointment.patient_id == User.id)
            .filter(Appointment.schedule_date == selected_date)
            .all()
        )
        if not appointments:
            flash(f'Không tìm thấy danh sách bệnh nhân đăng ký ngày {formatted_date} ')
        # lấy thông tin danh sách khám ngày đó đã có y tá quản lý chưa?
        appointment_list = AppointmentList.query.filter_by(schedule_date=selected_date).first()

    # Lấy danh sách các ngày đã lập lịch khám
    managed_days = AppointmentList.query.filter_by(nurse_id=current_user.id).all()
    return render_template('appointment/list_appointment.html',
                           appointments=appointments,
                           selected_date=formatted_date,
                           appointment_list=appointment_list,
                           managed_days=managed_days)


@app.route('/api/confirm-appointment/<schedule_date>', methods=['POST'])
def confirm_appointment(schedule_date):
    # Kiểm tra xem danh sách lịch khám đã tồn tại chưa
    appointment_list = AppointmentList.query.filter_by(schedule_date=schedule_date).first()

    if not appointment_list:
        # Nếu không có danh sách khám, tạo mới danh sách khám
        appointment_list = AppointmentList(schedule_date=schedule_date, nurse_id=current_user.id)
        db.session.add(appointment_list)
        db.session.commit()

    # Gắn các cuộc hẹn vào danh sách này và thay đổi trạng thái thành 'confirmed'
    appointments = Appointment.query.filter_by(schedule_date=schedule_date, status=Status.PENDING).all()
    for appointment in appointments:
        appointment.appointment_list_id = appointment_list.id
        appointment.status = Status.CONFIRMED

    db.session.commit()

    return jsonify({
        'message': f'Danh sách lịch khám ngày {schedule_date} đã được xác nhận thành công!',
        'appointment_list_id': appointment_list.id
    }), 200


@app.route('/api/send-mail-appointment/<schedule_date>', methods=['POST'])
def send_mail_appointment(schedule_date):
    # Truy vấn các bệnh nhân có lịch khám vào ngày schedule_date và trạng thái là CONFIRMED
    appointments = Appointment.query.filter_by(
        schedule_date=schedule_date,
        status=Status.CONFIRMED
    ).all()

    if not appointments:
        return jsonify({"message": "Không tìm thấy lịch hẹn xác nhận cho ngày đã chọn"}), 404

    # Tạo workbook Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh sách khám bệnh"

    # Tiêu đề danh sách
    ws.append(["DANH SÁCH KHÁM BỆNH"])
    ws.append([f"Ngày khám: {schedule_date}"])
    ws.append([])  # Dòng trống

    # Tiêu đề các cột
    headers = ["STT", "Họ tên", "Giới tính", "Năm sinh", "Địa chỉ"]
    ws.append(headers)

    # Duyệt qua các lịch khám để gửi email và thêm dữ liệu vào file Excel
    for index, appoint in enumerate(appointments, start=1):
        patient = User.query.filter_by(id=appoint.patient_id).first()

        # Gửi email nếu email hợp lệ
        if patient and patient.email:
            subject = f"Thông báo lịch hẹn khám vào {appoint.schedule_date} lúc {appoint.schedule_time}"
            body = f"""
            Kính gửi {patient.name},

            Lịch hẹn khám của bạn đã được xác nhận vào ngày {appoint.schedule_date} lúc {appoint.schedule_time}.

            Mã lịch khám của bạn là {appoint.id}

            Vui lòng đến trước 15 phút để hoàn tất thủ tục trước khi khám.

            Cảm ơn bạn đã chọn phòng khám của chúng tôi. Chúng tôi rất mong được gặp bạn!

            Trân trọng,
            Đội ngũ phòng khám Sài Gòn Care.
            """
            try:
                msg = Message(subject, recipients=[patient.email], sender='phongkhamsaigoncare@gmail.com')
                msg.body = body
                mail.send(msg)
            except Exception as e:
                flash(f"Lỗi khi gửi email đến {patient.name}: {str(e)}")

        # Thêm dữ liệu bệnh nhân vào file Excel
        row = [
            index,
            patient.name,
            "Nam" if patient.gender == Gender.MALE else "Nữ",
            patient.dob.year,
            patient.address
        ]
        ws.append(row)

    # Định dạng file Excel (căn giữa cột và điều chỉnh độ rộng)
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter  # Lấy tên cột (A, B, C, ...)
        for cell in col:
            try:
                max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[col_letter].width = max_length + 2

    # Xuất file Excel dưới dạng response
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = make_response(output.read())
    response.headers["Content-Disposition"] = f"attachment; filename=Danh_sach_kham_{schedule_date}.xlsx"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return response


@app.route('/medical_details', methods=['GET', 'POST'])
@login_required
def medical_details():
    patient_info = None
    drugs_search = []
    units = Unit.query.all()
    types = Type.query.all()
    drug = Drug.query.all()
    patient_appoint = None
    current_time = datetime.now() + timedelta(minutes=15)
    drug_list = []
    page = request.args.get('page', 1)
    counter = dao.count_drugs()

    # lấy thông tin bênh nhân từ csdl -> form (thông qua partient_id)
    if request.method.__eq__('POST'):
        action = request.form.get('action')
        patient_id = request.form.get('patient_id')
        if patient_id:
            patient_info = User.query.filter_by(id=patient_id).first()
            patient_appoint = Appointment.query.filter_by(patient_id=patient_id, status=Status.CONFIRMED).first()
        # Hành động tìm kiếm bệnh nhân
        if action == 'search_appointment':
            appointment_id = request.form.get('appointment_id', "").strip()
            patient_appoint = Appointment.query.filter_by(id=appointment_id).first() #Lấy lịch khám đầu tiên trong  danh sách khám
            if patient_appoint and patient_appoint.status == Status.CONFIRMED:
                patient_info = User.query.filter_by(id=patient_appoint.patient_id).first()

                patient_schedule_datetime = datetime.strptime(
                    f"{patient_appoint.schedule_date} {patient_appoint.schedule_time}",
                    "%Y-%m-%d %H:%M:%S"
                )
                # Kiểm tra bệnh nhân đủ điều kiện khám bệnh. Trễ 15p so với thời gian đã đặt liịch.
                if patient_schedule_datetime <= current_time:
                    patient_appoint.status = Status.CANCELED
                    db.session.commit()
                    flash("Lịch hẹn bệnh nhân đã quá hạn!")
                    return render_template('medical_details/add_medical_details.html', patient_info=None,
                                           patient_appoint=None, drug=drug, units=units, types=types,
                                           drugs_search=drugs_search,
                                           page=math.ceil(counter / app.config['PAGE_SIZE'])
                                           )
                # tạm thời để not ở if dữ liệu để kiểm tra.
                else:
                    pass
            else:  # lay ten benh nhan
                flash("Không tìm thấy thông tin bệnh nhân hoặc lịch khám")
                return render_template('medical_details/add_medical_details.html', patient_info=None,
                                       patient_appoint=None, drug=drug, units=units, types=types,
                                       drugs_search=drugs_search,
                                       page=math.ceil(counter / app.config['PAGE_SIZE'])
                                       )
        elif action == 'search_drug':
            drug_unit = request.form.get('units')
            drug_type = request.form.get('types')
            drug_name = request.form.get('drug_name')
            drug_info = Drug.query.filter_by(name=drug_name,
                                             drugType=drug_type,
                                             drugUnit=drug_unit).first()

            # if drug_info:  # có thông tin thuốc trong csdl
            drugs_search = dao.load_drugs(
                name=drug_name,
                unit=drug_unit,
                type=drug_type,
                page=int(page)
            )

            if not drugs_search:
                flash('Không tìm thấy thuốc đã nhập')
            return render_template('medical_details/add_medical_details.html',
                                   patient_info=patient_info,
                                   patient_appoint=patient_appoint,
                                   drug=drug,
                                   units=units,
                                   types=types,
                                   drug_list=drug_list,
                                   drugs_search=drugs_search,
                                   page=math.ceil(counter / app.config['PAGE_SIZE'])
                                   )
            # drug_quantity = int(request.form.get('quantity'))
            # drug_description = request.form.get('description')
            # temp = drug_info.quantity - drug_quantity
            # if temp > 0:
            #     drug_detail = {
            #         'name': drug_name,
            #         'type': drug_type,
            #         'unit': drug_unit,
            #         'quantity': drug_quantity,
            #         'description': drug_description
            #     }
            #     # Thêm drug_detail vào danh sách drug_list
            #     drug_list.append(drug_detail)
            # else:
            #     flash('Số lượng thuốc trong kho đã hết!')
        # else:
        #     flash('Không tìm thấy thuốc đã nhập!')

    return render_template('medical_details/add_medical_details.html',
                           patient_info=patient_info,
                           patient_appoint=patient_appoint,
                           drug=drug,
                           units=units,
                           types=types,
                           drug_list=drug_list,
                           drugs_search=drugs_search,
                           page=math.ceil(counter / app.config['PAGE_SIZE'])
                           )


# @app.route('/api/add-drug', methods=['POST'])
# def add_drug_list():
#     # Lấy thông tin thuốc từ request
#     name = request.json.get('name')
#     type = int(request.json.get('type'))  # Chuyển đổi kiểu dữ liệu về int
#     unit = int(request.json.get('unit'))  # Chuyển đổi kiểu dữ liệu về int
#     quantity = int(request.json.get('quantity'))
#     description = request.json.get('description')
#     drug_id = None
#     if not description or not quantity:
#         return jsonify({'message': 'Không được để trống thông tin quantity và description'}), 404
#         # flash("Không được để trống thông tin!")
#         # return redirect(url_for('medical_details'))
#     drug = Drug.query.filter_by(name=name, drugType=type, drugUnit=unit).first()
#
#     sum_drug_details = DrugDetail.query.filter_by(drug=drug.id)
#     if drug.quantity - quantity <= 0:
#         return jsonify({'message': 'Số lượng thuốc trong kho đã đạt giới hạn'})
#     if drug:
#         drug_id = drug.id
#     else:
#         return jsonify({'message': 'Drug not found'}), 404
#     # Kiểm tra và lấy drug_list từ session
#     drug_list = session.get('drug_list', {})
#
#     # Loại bỏ key không hợp lệ ('null') nếu có
#     if 'null' in drug_list:
#         del drug_list['null']
#
#     # Kiểm tra xem thuốc đã có trong danh sách chưa
#     if str(drug_id) in drug_list:
#         drug_list[str(drug_id)]['quantity'] += quantity  # Cập nhật số lượng
#         drug_list[str(drug_id)]['description'] = description or ''
#     else:
#         drug_list[str(drug_id)] = {
#             'drug_id': drug_id,
#             'name': name,
#             'type': type,
#             'unit': unit,
#             'quantity': quantity,
#             'description': description or ''
#         }
#     # Lưu lại danh sách thuốc vào session
#     session['drug_list'] = drug_list
#     print(f"Drug list updated: {drug_list}")
#
#     # Trả về danh sách thuốc đã cập nhật
#     return jsonify({'message': 'Drug added successfully'})

@app.route('/api/add-drug', methods=['POST'])
def add_drug_list():
    # Lấy thông tin thuốc từ request
    name = request.json.get('name')
    type = int(request.json.get('type'))  # Chuyển đổi kiểu dữ liệu về int
    unit = int(request.json.get('unit'))  # Chuyển đổi kiểu dữ liệu về int
    quantity = int(request.json.get('quantity'))
    description = request.json.get('description')

    # Kiểm tra các thông tin bắt buộc
    if not description or quantity <= 0:
        return jsonify({'message': 'Thông tin quantity và description không hợp lệ'}), 400

    # Lấy thông tin thuốc từ cơ sở dữ liệu
    drug = Drug.query.filter_by(name=name, drugType=type, drugUnit=unit).first()

    if not drug:
        return jsonify({'message': 'Không tìm thấy thuốc'}), 404

    # Tính tổng số lượng đã sử dụng của thuốc từ bảng DrugDetail
    from sqlalchemy.sql import func
    total_used_quantity = db.session.query(func.sum(DrugDetail.quantity)) \
                              .filter(DrugDetail.drug == drug.id) \
                              .scalar() or 0

    # Kiểm tra số lượng tồn kho
    available_quantity = drug.quantity - total_used_quantity
    print(f'số lượng tồn kho: {available_quantity}')

    if available_quantity <= 0:
        return jsonify({'message': 'Thuốc trong kho đã hết'}), 400

    if quantity > available_quantity:
        return jsonify({'message': f'Số lượng thuốc còn lại không đủ. Chỉ còn {available_quantity} đơn vị'}), 400

    # Kiểm tra và lấy drug_list từ session
    drug_list = session.get('drug_list', {})

    # Cập nhật thông tin vào drug_list
    if str(drug.id) in drug_list:
        drug_list[str(drug.id)]['quantity'] += quantity
        drug_list[str(drug.id)]['description'] = description or drug_list[str(drug.id)]['description']
    else:
        drug_list[str(drug.id)] = {
            'drug_id': drug.id,
            'name': drug.name,
            'type': drug.drugType,
            'unit': drug.drugUnit,
            'quantity': quantity,
            'description': description
        }

    # Lưu drug_list vào session
    session['drug_list'] = drug_list

    return jsonify({'message': 'Thêm thuốc thành công', 'drug_list': list(drug_list.values())}), 200


@app.route('/api/delete-drug-detail/<drug_detail_id>', methods=['DELETE'])
def delete_drug_detail(drug_detail_id):

    # Kiểm tra xem drug_list có trong session không
    drug_list = session.get('drug_list', {})

    # Kiểm tra nếu drug_detail_id có trong drug_list
    if drug_detail_id and drug_detail_id in drug_list:
        del drug_list[drug_detail_id]  # Xóa thuốc khỏi danh sách
        session['drug_list'] = drug_list  # Lưu lại danh sách đã cập nhật
        return jsonify({'message': 'Drug detail deleted successfully'}), 200
    else:
        return jsonify({'message': 'Drug detail not found'}), 404


@app.route('/api/clear-drug-list', methods=['POST'])
def clear_drug_list():
    if 'drug_list' in session:
        del session['drug_list']
        return jsonify({'message': 'Đã xóa drug_list.'}), 200
    else:
        return jsonify({'message': 'Không có drug_list trong session.'}), 400


# chưa làm edit_drug_list()

@app.route('/api/add-medical-details', methods=['POST'])
def add_medical_details():
    # Lấy thông tin từ request
    patient_id = int(request.json.get('patient_id'))
    appoint_id = int(request.json.get('appoint_id'))
    symptoms = request.json.get('symptoms')
    diagnose = request.json.get('diagnose')
    doctor_id = int(request.json.get('doctor_id'))
    # Tạo đối tượng MedicalDetails
    new_medical_detail = MedicalDetails(
        patient_id=patient_id,
        doctor_id=doctor_id,
        symptoms=symptoms,
        diagnose=diagnose,
        total=0.0  # Tổng tiền ban đầu là 0, sẽ tính sau
    )

    # Lưu MedicalDetails vào database
    db.session.add(new_medical_detail)
    db.session.commit()

    # Kiểm tra xem drug_list có trong session không
    drug_list = session.get('drug_list', {})

    total_price = app.config['SUM']  # Tổng tiền của tất cả thuốc

    # Nếu có drug_list, thêm thuốc vào DrugDetail và tính tổng tiền
    if drug_list:
        for drug_id, drug_info in drug_list.items():
            # Lấy thông tin thuốc từ bảng Drug
            drug = Drug.query.get(drug_id)
            print("hahahha")
            print(drug_info['quantity'])
            print(drug_info['description'])
            if drug:
                # Tạo mới DrugDetail
                drug_detail = DrugDetail(
                    medicalDetails=new_medical_detail.id,
                    drug=drug.id,
                    quantity=drug_info['quantity'],
                    description=drug_info['description']
                )

                # Tính tổng tiền cho mỗi loại thuốc
                total_price += drug.price * drug_info['quantity']

                # Lưu DrugDetail vào database
                db.session.add(drug_detail)

        # Cập nhật tổng tiền cho MedicalDetails
        new_medical_detail.total = total_price
        db.session.commit()
        # thay đổi trang thái lịch khám
        appoint = Appointment.query.filter_by(id=appoint_id).first()
        appoint.status = Status.COMPLETED
        db.session.commit()

        # Xóa drug_list khỏi session sau khi đã xử lý
        session.pop('drug_list', None)
    else:
        return jsonify({'message': 'Chưa khởi tạo đơn thuốc'}),400

    return jsonify({'message': 'Lập phiếu khám thành công', 'total': total_price}), 200



# @app.route('/info-medical-detail/<int:id>', methods=['GET','POST'])
# def info_medical_detail(id):
#     # Lấy chi tiết khám vừa mới đăng ký
#     info_medical = MedicalDetails.query.filter_by(id=id).first()
#     if not info_medical:
#         return "Không tìm thấy phiếu khám", 404
#
#     # Lấy danh sách thuốc liên quan (nếu có)
#     drug_details = DrugDetail.query.filter_by(medicalDetails=info_medical.id).all()
#
#     # Trả về template với medical_detail và drug_details
#     return render_template('medical_details/info_medical_details.html',
#                            medical_detail=info_medical,
#                            drugs=drug_details)
#
#
# @app.route('/api/add-medical-details', methods=['POST'])
# def add_medical_details():
#     # # Lấy thông tin từ request
#     # patient_id = int(request.json.get('patient_id'))
#     # appoint_id = int(request.json.get('appoint_id'))
#     # symptoms = request.json.get('symptoms')
#     # diagnose = request.json.get('diagnose')
#     # doctor_id = int(request.json.get('doctor_id'))
#     #
#     # # Kiểm tra xem drug_list có trong session không
#     # drug_list = session.get('drug_list', {})
#     # if not drug_list:
#     #     return jsonify({'message': 'Chưa khởi tạo đơn thuốc'}), 400
#     #
#     # # Tạo đối tượng MedicalDetails
#     # new_medical_detail = MedicalDetails(
#     #     patient_id=patient_id,
#     #     doctor_id=doctor_id,
#     #     symptoms=symptoms,
#     #     diagnose=diagnose,
#     #     total=0.0  # Tổng tiền ban đầu là 0, sẽ tính sau
#     # )
#     #
#     # # Lưu MedicalDetails vào database
#     # db.session.add(new_medical_detail)
#     # db.session.commit()
#     #
#     # total_price = app.config['SUM']  # Tổng tiền của tất cả thuốc
#     #
#     # # Nếu có drug_list, thêm thuốc vào DrugDetail và tính tổng tiền
#     # for drug_id, drug_info in drug_list.items():
#     #     # Lấy thông tin thuốc từ bảng Drug
#     #     drug = Drug.query.filter_by(id=drug_id).first()
#     #     if drug:
#     #         # Tạo mới DrugDetail
#     #         drug_detail = DrugDetail(
#     #             medicalDetails=new_medical_detail.id,
#     #             drug=drug.id,
#     #             quatity=drug_info['quantity'],
#     #             description=drug_info['description']
#     #         )
#     #
#     #         # Tính tổng tiền cho mỗi loại thuốc
#     #         total_price += drug.price * drug_info['quantity']
#     #
#     #         # Lưu DrugDetail vào database
#     #         db.session.add(drug_detail)
#     #
#     # # Cập nhật tổng tiền cho MedicalDetails
#     # new_medical_detail.total = total_price
#     # db.session.commit()
#     #
#     # # Thay đổi trạng thái lịch khám
#     # appoint = Appointment.query.filter_by(id=appoint_id).first()
#     # appoint.status = Status.COMPLETED
#     # db.session.commit()
#     #
#     # # Xóa drug_list khỏi session sau khi đã xử lý
#     # session.pop('drug_list', None)
#
#     # Redirect đến trang chi tiết của MedicalDetails vừa tạo
#     return redirect(url_for('info_medical_detail', id=22))

@login_required
@app.route('/history-medical-detail', methods=['POST', 'GET'])
def history_medical_detail():
    patient_info = None
    history_medical = []
    user = User.query.all()
    drug = Drug.query.all()
    drug_details = DrugDetail.query.all()
    # Kiểm tra vai trò người dùng
    if current_user.user_role == UserRole.PATIENT:
        patient_info = current_user

    # Nếu là bác sĩ, lấy patient_id từ tham số URL
    if current_user.user_role == UserRole.DOCTOR:
        patient_id = request.args.get('patient_id', type=int)
        print(f"Received patient_id: {patient_id}")  # In ra để kiểm tra
        patient_info = User.query.filter_by(id=patient_id).first()

    if not patient_info:
        flash('Không có dữ liệu về bệnh nhân!')
    else:
        history_medical = MedicalDetails.query.filter_by(patient_id=patient_info.id).all()
    return render_template('patient/history_medical_detail.html', patient_info=patient_info,
                           history_medical=history_medical,
                           user=user)

@app.route('/view-history-detail', methods=['GET'])
@login_required
def view_history_detail():
    medical_id = request.args.get('medical_id', type=int)
    if not medical_id:
        flash("Không tìm thấy thông tin chi tiết lịch sử khám bệnh!", "warning")
        return redirect(url_for('history_medical_details'))

    # Truy vấn thông tin chi tiết khám bệnh
    medical_details = MedicalDetails.query.filter_by(id=medical_id).first()
    if not medical_details:
        flash("Không tìm thấy lịch sử khám bệnh!", "danger")
        return redirect(url_for('history_medical_details'))

    # Truy vấn danh sách đơn thuốc
    drug_details = DrugDetail.query.filter_by(medicalDetails=medical_id).all()

    # Lấy thông tin thuốc
    drugs = {d.id: d for d in Drug.query.all()}

    return render_template('patient/view_detail_history.html',
                           medical_details=medical_details,
                           drug_details=drug_details,
                           drugs=drugs,
                           user=User.query.all())

@app.route('/payment', methods=['get', 'post'])
# @nursesnotloggedin
def payment():
    mes = ""
    info = None
    total = 0

    if request.method.__eq__('POST'):
        medical_id = request.form.get('k')
        # print("TMP")
        print(medical_id)
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
                # print("haha")
                # print(medical_id)
                # print(info)
                # print(drug_list)
                total = utils.total(medical_id)
                user_doctor = None
                if m and info and drug_list:
                    if u.user_role.value == 'patient':
                        user_doctor = dao.get_user(info[1].id)
                else:
                    mes = "Không có đơn thuốc"
                return render_template('payment/payment.html', user=u, info=info, drug_list=drug_list,
                                           doctor=user_doctor,tiendu = tiendu, mes = mes, total=total)
        else:
                mes = "Không tìm thấy không tin"
    return render_template('payment/payment.html', mes=mes)





@app.route('/payment_return_vnpay', methods=['GET','POST'])
# @nursesnotloggedin
def payment_return():
    inputData = request.args
    vnp = vnpay.VNpay()
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
            pOnline = dao.get_online_payment(payment_id)
            print(p)
            if p:
                p.trangthai = "Condition.PAID"
                db.session.commit()

                pOnline.idGiaoDich = transtraction_id
                # p.idGiaoDich = str(transtraction_id)
                print("p.idGiaoDich")

                db.session.commit()

            print("Thanh toán thành công!")
            return render_template('/payment/returnAPI.html')

    else:
        # Xử lý trường hợp lỗi từ VNPAY
        print("Loi")
        return redirect('/')







@app.route('/api/bills', methods=['GET', 'POST'])
def create_bill():
    if request.method.__eq__('POST'):
        print("Do create_bill")
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
        print("Medical")
        print(info[0].id)

        if type == "radio_offline":
            tientra_off = utils.total(info[0].id)
            print(tientra_off)

        p = None
        if type == "radio_offline":
            print(1)
            p = dao.add_payment(date = datetime.now(), sum = tientra_off, nurse_id = current_user.id, medical_id = info[0].id, loai = type,
                                idGiaoDich = None)  #fix lai xem sao de lam cho y ta dung
        else:
            print(2)
            p =dao.add_payment(date=datetime.now(), sum=tientra, nurse_id=current_user.id, medical_id=info[0].id,
                                idGiaoDich=None, loai = type)
        # print(p)# fix lai xem sao de lam cho y ta dung
        db.session.add(p)
        db.session.commit()
        print("Xong ")
    return render_template('index.html')



@app.route('/paymentlist', methods=['GET', 'POST'])
def paymentlist():
    print("Do pm list")
    mess = ""
    payment = None
    id = current_user.id
    info = dao.get_info(id)
    # print("paymentlist")
    print("Info dt")
    print(type(info))
    if isinstance(info, Row):
        print(1)
        payment = dao.get_payment(medical_id=info[0].id)

    # print(payment)
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
        # total = utils.total(medical_id= info[0].id)
        # print(1)
        # print(drug_list)
        # print(info)
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
        vnp = vnpay.VNpay()
        vnp.requestData['vnp_Version'] = '2.1.0'
        vnp.requestData['vnp_Command'] = 'pay'
        vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
        vnp.requestData['vnp_OrderInfo'] = order_desc
        vnp.requestData['vnp_OrderType'] = order_type
        # Check language, default: vn

        vnp.requestData['vnp_Locale'] = 'vn'
        ipaddr = request.remote_addr
        # Build URL Payment
        vnp = vnpay.VNpay()
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
        # return redirect(vnpay_payment_url)
        return render_template(vnpay_payment_url)
    else:
        return render_template('payment/payment.html', title="Thanh toán")





if __name__ == "__main__":
    # nạp trang admin
    from clinic.admin import *

    app.run(debug=True)
