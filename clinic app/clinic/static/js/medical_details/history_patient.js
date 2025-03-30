function view_history_medical_detail(){
     let patient_id = document.getElementById('patient_id').value;
     alert('patient_id: ' + patient_id)
     if(patient_id) {
     // Chuyển hướng tới route với patient_id
         window.location.assign = '/history-medical-detail?patient_id=' + patient_id;
     }
     else{
     alert('Chưa có thông tin bệnh nhân !!')
     }

}