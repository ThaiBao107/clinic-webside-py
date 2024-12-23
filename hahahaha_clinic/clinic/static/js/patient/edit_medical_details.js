
function saveMedicalDetail() {
    // Lấy dữ liệu từ form
    let formData = new FormData();
    formData.append('patient_id', document.getElementById('patient_id').value);
    formData.append('symptoms', document.getElementById('symptoms').value);
    formData.append('diagnose', document.getElementById('diagnose').value);

    // Gửi request POST đến server
    fetch('/medical_details', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            alert('Lưu thông tin thành công!');
            // Có thể thêm code để reset form hoặc redirect
            document.getElementById('medicalDetailForm').reset();
        } else {
            alert('Có lỗi xảy ra: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Có lỗi xảy ra khi lưu thông tin');
    });
}