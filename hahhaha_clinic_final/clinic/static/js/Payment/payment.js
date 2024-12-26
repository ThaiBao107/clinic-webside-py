function displayOfflinePayment() {
    document.getElementById("online_payment").style.display = "none";

    var content = document.getElementById("xuat-hoa-don");

    while (content.firstChild) {
        content.removeChild(content.lastChild);
    }

    var divTienNhan = document.createElement("div");
    divTienNhan.setAttribute("class", "form-floating mb-3 mt-3");
    content.appendChild(divTienNhan);

    var inputTienNhan = document.createElement("input");
    var inputTotal = document.getElementById('total')
    inputTienNhan.setAttribute("type", "number");
    inputTienNhan.setAttribute("class", "form-control");
    inputTienNhan.setAttribute("id", "tien_nhan");
    inputTienNhan.setAttribute("required", "True");
    inputTienNhan.setAttribute("min", inputTotal.value);
    inputTienNhan.setAttribute("placeholder", "Nhập tiền nhận");
    inputTienNhan.setAttribute("name", "tien_nhan");
    inputTienNhan.addEventListener("input", () => {
        var total = document.getElementById("total");
        var inputTienThoi = document.getElementById("tien_thoi");
        inputTienNhan.setAttribute("value", inputTienNhan.value);
        inputTienThoi.setAttribute("value", (inputTienNhan.value - parseFloat(total.innerText)));
    });
    divTienNhan.appendChild(inputTienNhan);
    var tiennhan1 = document.getElementById('tien_nhan')
    var labelTienNhan = document.createElement("label");
    labelTienNhan.setAttribute("for", "tien_nhan");
    labelTienNhan.innerHTML = "Tiền Nhận"
    divTienNhan.appendChild(labelTienNhan);

    var divTienThoi = document.createElement("div");
    divTienThoi.setAttribute("class", "form-floating mb-3 mt-3");
    content.appendChild(divTienThoi);

    var inputTienThoi = document.createElement("input");
    inputTienThoi.setAttribute("type", "number");
    inputTienThoi.setAttribute("class", "form-control");
    inputTienThoi.setAttribute("id", "tien_thoi");
    inputTienThoi.setAttribute("placeholder", "Nhập tiền thối");
    inputTienThoi.setAttribute("name", "tien_thoi");
    inputTienThoi.setAttribute("readonly", "true");
    divTienThoi.appendChild(inputTienThoi);

    var labelTienThoi = document.createElement("label");
    labelTienThoi.setAttribute("for", "tien_thoi");
    labelTienThoi.innerHTML = "Tiền Thối"
    divTienThoi.appendChild(labelTienThoi);

    var divXacNhan = document.createElement("div");
    divXacNhan.setAttribute("class", "form-floating mb-3 mt-3 d-flex flex-row-reverse");
    divXacNhan.setAttribute("id", "xacnhan");
    content.appendChild(divXacNhan);



}



function displayOnlinePayment() {
    var content = document.getElementById("xuat-hoa-don");
    while (content.firstChild) {
        content.removeChild(content.lastChild);
    }
    document.getElementById("online_payment").style.display = "block";
    var divTienNhan = document.createElement("div");
    divTienNhan.setAttribute("class", "form-floating mb-3 mt-3");
    content.appendChild(divTienNhan);

    var inputTienNhan = document.createElement("input");
    var inputTotal = document.getElementById('total')
    inputTienNhan.setAttribute("type", "number");
    inputTienNhan.setAttribute("class", "form-control");
    inputTienNhan.setAttribute("id", "tien_nhan");
    inputTienNhan.setAttribute("required", "True");
    inputTienNhan.setAttribute("min", inputTotal.value);
    inputTienNhan.setAttribute("placeholder", "Nhập tiền muốn trả:");
    inputTienNhan.setAttribute("name", "tien_nhan");
    inputTienNhan.addEventListener("input", () => {
        var total = document.getElementById("total");

        var inputTienThoi = document.getElementById("tien_thoi");
        inputTienNhan.setAttribute("value", inputTienNhan.value);
        inputTienThoi.setAttribute("value", Math.abs((inputTienNhan.value - parseFloat(total.innerText))));
    });
    divTienNhan.appendChild(inputTienNhan);

    var labelTienNhan = document.createElement("label");
    labelTienNhan.setAttribute("for", "tien_nhan");
    labelTienNhan.innerHTML = "Tiền muốn trả"
    divTienNhan.appendChild(labelTienNhan);

    var divTienThoi = document.createElement("div");
    divTienThoi.setAttribute("class", "form-floating mb-3 mt-3");
    content.appendChild(divTienThoi);

    var inputTienThoi = document.createElement("input");
    inputTienThoi.setAttribute("type", "number");
    inputTienThoi.setAttribute("class", "form-control");
    inputTienThoi.setAttribute("id", "tien_thoi");
    inputTienThoi.setAttribute("placeholder", "Tiền còn thiếu");
    inputTienThoi.setAttribute("name", "tien_thoi");
    inputTienThoi.setAttribute("readonly", "true");
    divTienThoi.appendChild(inputTienThoi);

    var labelTienThoi = document.createElement("label");
    labelTienThoi.setAttribute("for", "tien_thoi");
    labelTienThoi.innerHTML = "Tiền còn thiếu"
    divTienThoi.appendChild(labelTienThoi);

       // Dữ liệu gửi lên server

}

function a()
{
    var total = document.getElementById("total_info")
    alert(total.value)
}





function checkPaymentStatus() {
    const queryParams = new URLSearchParams(window.location.search);

    fetch('/payment_return_vnpay' + queryParams.toString(), {
        method: 'GET', // GET vì chỉ cần kiểm tra
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Không thể kiểm tra trạng thái thanh toán.');
        }
    })
    .then(data => {
        console.log(data);
        if (data.success) {
            alert('Thanh toán thành công!');
        } else {
            alert('Thanh toán thất bại!');
        }
    })
    .catch(error => {
        console.error('Lỗi khi kiểm tra trạng thái thanh toán:', error);
    });
}

function mes()
{
    alert("Tạo đơn hàng công")

    var type = ""
    var id = document.getElementsByName('user_id')[0]
    var display = document.getElementsByName("optradio")
    for(var i = 0; i< display.length; i++)
        if (display[i].checked)
            if(display[i].value === "radio_online")
                type = display[i].value

            else
                type = display[i].value
    alert(id)
    alert(type)
    var tientra = ""
    if (type === "radio_online")
        tientra = document.getElementById("tien_nhan")

    var data = {user_id:id.value , type_payment : type, tien_tra:tientra.value}
     fetch('/api/bills', {
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
                throw new Error('Gui khong thanh cong');
            }
        })
        .then(data => {
            console.log( data);
            if (data.payment_url) {
                // Redirect tới URL của VNPAY
                window.location.href = data.payment_url;
            }
        })
        .catch(error => {
            console.error('Lỗi khi gọi API', error);
        });
}


function GetPaymentId(){
     fetch('/api/bills', {
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
                throw new Error('Gui khong thanh cong');
            }
        })
        .then(data => {
            console.log( data);
            if (data.payment_url) {
                // Redirect tới URL của VNPAY
                window.location.href = data.payment_url;
            }
        })
        .catch(error => {
            console.error('Lỗi khi gọi API', error);
        });
}


