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
