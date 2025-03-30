function callPaymentAPI() {
    // alert("Online payment")
    // Gọi API
    var total = document.getElementById("total")
     // Lấy phần tử <p id="total">
    var totalValue = total.textContent;
    var data = {total:totalValue}
    alert(totalValue)
    fetch('/api/process_vnpay', {
        method: 'POST', // POST vì có dữ liệu gửi lên
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data), // Chuyển dữ liệu thành JSON
    })
        .then(response => {
            if (response.ok) {
                return response.json(); // Nếu trả về JSON thì xử lý
            } else {
                throw new Error('Thanh toán thất bại.');
            }
        })
        .then(data => {
            console.log("h1" + data);
            if (data.payment_url) {
                // Redirect tới URL của VNPAY
                window.location.href = data.payment_url;
            }
        })
        .catch(error => {
            console.error('Lỗi khi gọi API thanh toán:', error);
        });
    //xu ly giao dien online payment va goi api online payment o day
    //dung content de xu ly giao dien
}