function deleteAppointment(id) {
    if (confirm("Bạn chắc chắn muốn xóa lịch khám này không?") === true) {
        fetch('/api/delete-appointment/' + id, {
            method: 'DELETE',
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.message.includes("successfully")) {
                    // Xóa dòng khỏi bảng
                    const row = document.querySelector(`#appointment-${id}`);
                    if (row) row.remove();

                    // Kiểm tra nếu bảng rỗng
                    const tableBody = document.querySelector('.appointment-list tbody');
                    if (tableBody.children.length === 0) {
                        // Hiển thị thông báo nếu không còn lịch khám
                        const noAppointments = document.createElement('p');
                        noAppointments.textContent = 'Bạn chưa đăng ký lịch khám nào.';
                        noAppointments.className = 'text-center text-danger';
                        document.querySelector('.appointment-list').appendChild(noAppointments);
                        document.querySelector('.table').remove(); // Ẩn bảng
                    }
                }
            })
            .catch(error => console.error('Error:', error));
    }
}

//Xử lý ngày giờ khám
document.addEventListener("DOMContentLoaded", () => {
    // Tạo danh sách giờ khám
    const appointmentTimeSelect = document.getElementById("schedule_time");
    const startHour = 7; // 7h sáng
    const endHour = 19; // 7h tối
    const interval = 15; // 15 phút

    for (let hour = startHour; hour < endHour; hour++) {
        for (let minute = 0; minute < 60; minute += interval) {
            const time = `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
            const option = document.createElement("option");
            option.value = time;
            option.textContent = time;
            appointmentTimeSelect.appendChild(option);
        }
    }
    // xử lý ngày khám
       // Lấy ngày hiện tại và tính ngày hôm qua
        const today = new Date();
        today.setDate(today.getDate());
        const day = today.getDate().toString().padStart(2, '0'); // Thêm số 0 cho ngày
        const month = (today.getMonth() + 1).toString().padStart(2, '0'); // Thêm số 0 cho tháng
        const year = today.getFullYear();
        const yesterday = `${year}-${month}-${day}`;
        const appointmentDateInput = document.getElementById("schedule_date");
        appointmentDateInput.setAttribute("min", yesterday);  // Không cho phép chọn ngày hôm qua và sau đó
});
