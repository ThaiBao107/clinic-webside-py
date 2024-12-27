function add_drug_list() {
    let name = document.getElementById('drug_name').value;
    let type = document.getElementById('type').value;
    let unit = document.getElementById('units').value;
    let quantity = document.getElementById('quantity').value;
    let description = document.getElementById('description').value;
    fetch('/api/add-drug', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'name': name,
            'type': type,
            'unit': unit,
            'quantity': quantity,
            'description': description
        })
    })
     .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Lỗi: ${data.error}`);
            } else {
                alert(data.message);
               window.location.reload();

            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Đã xảy ra lỗi khi tạo danh sách.');
        });
}
function reset_drug_list(){

  fetch('/api/clear-drug-list', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
      .then(data => {
          location.reload();  // Tải lại trang để cập nhật giao diện
          console.log('Đã xóa drug_list cũ:', data.message);
          // Sau khi xóa drug_list, gửi form tìm kiếm bệnh nhân
          document.querySelector('form').submit();
      })
      .catch(error => {
          console.error('Lỗi khi xóa drug_list:', error);
      });
}

function delete_drug_detail(drug_detail_id) {
    fetch(`/api/delete-drug-detail/${drug_detail_id}`, {
        method: 'DELETE',  // Dùng phương thức DELETE
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Drug detail deleted successfully') {
            alert('Đã xóa thuốc khỏi danh sách!');
            window.location.reload(); // Tải lại trang để cập nhật danh sách thuốc
        } else {
            alert('Không tìm thấy thuốc cần xóa!');
        }
    })
    .catch(error => {
        console.error('Lỗi:', error);
        alert('Đã xảy ra lỗi khi xóa thuốc.');
    });
}

function add_medical_details()
{
  let patient_id =  document.getElementById('patient_id').value;
  let appoint_id =  document.getElementById('appoint_id').value;
  let symptoms =  document.getElementById('symptoms').value;
  let diagnose =  document.getElementById('diagnose').value;
  let doctor_id =  document.getElementById('current_user_id').value;
 if (!patient_id || !appoint_id || !diagnose || !symptoms) {
        // Hiển thị thông báo lỗi nếu có trường rỗng
        alert("Vui lòng điền đầy đủ thông tin:\n" +
            "Mã bệnh nhân: " + patient_id + "\n" +
            "Triệu chứng: " + symptoms + "\n" +
            "Chẩn đoán: " + diagnose);
    } else {

         alert("Đủ  thông  tin!")
          fetch('/api/add-medical-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'patient_id': patient_id,
            'appoint_id': appoint_id,
            'symptoms': symptoms,
            'diagnose': diagnose,
            'doctor_id': doctor_id
        })
    })
     .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Lỗi: ${data.error}`);
            } else {
                alert(data.message);
               window.location.reload();

            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Đã xảy ra lỗi khi tạo danh sách.');
        });
       }
}