# AsynapRous

A Python-based networking framework and application suite developed for the CO3093/CO3094 course at HCMC University of Technology VNU-HCM.

## Overview

AsynapRous provides a foundational framework to build, route, and serve RESTful web applications utilizing standard Python socket programming. The system is split into three main executable components:

- **Proxy Server (`start_proxy.py`)**: A reverse proxy that listens for incoming HTTP requests, parses virtual hosts from `config/proxy.conf`, and routes requests to the appropriate backend application using specified distribution policies (e.g., round-robin).
  - Default Binding: `0.0.0.0:8080`

- **Backend Daemon (`start_backend.py`)**: A backend server daemon entry point that handles raw HTTP processing using the core AsynapRous architecture, managing incoming traffic efficiently. 
  - Default Binding: `0.0.0.0:9000`

- **Sample Application (`start_sampleapp.py`)**: A practical demonstration of the REST framework providing example handlers (e.g., a login endpoint and greeting endpoints).
  - Default Binding: `0.0.0.0:2026`

## Architecture Highlights

The core of the server logic is contained in the `daemon/` and `apps/` packages:

- **`AsynapRous` Core**: Main HTTP server scaffolding.
- **Request & Response Utilities**: Modular parsing and rendering of standard HTTP requests.
- **NGINX-like Config**: Support for custom proxy configurations and basic routing strategies.

## Running the Components

All server components provide command-line arguments to customize the IP address and port mapping. 

To start the sample application locally:
```bash
python start_sampleapp.py --server-ip 127.0.0.1 --server-port 2026
```

To run the proxy server:
```bash
python start_proxy.py --server-ip 127.0.0.1 --server-port 8080
```

## Hướng dẫn Test (Thử nghiệm)

Mô-đun Authentication & User Management (Giai đoạn 2) đã được tích hợp lên Sample Application.
Để phục vụ việc kiểm tra và báo cáo kết quả, hãy thực hiện kịch bản test như sau:

**1. Khởi chạy Backend**
```bash
python start_sampleapp.py --server-ip 127.0.0.1 --server-port 2026
```

**2. Gửi lệnh Test Đăng nhập bằng `cURL` (mở cửa sổ CMD/PowerShell mới)**
```bash
curl -i -X POST http://127.0.0.1:2026/login -d "{\"username\": \"user1\", \"password\": \"pass1\"}"
```
Hoặc dùng Postman: gửi POST request vào `http://127.0.0.1:2026/login` với raw body dạng JSON (chứa `username` và `password`).

**3. Expected Output (Kết quả mong đợi)**
Sau khi đăng nhập thành công với một trong các user có sẵn (ví dụ `user1`/`pass1`), console của server sẽ log thông báo nhận được hook.
Về phía Client, HTTP Response trả về sẽ trông giống như sau (bao gồm Header và Body):

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 72
Set-Cookie: session_id=123e4567-e89b-12d3-a456-426614174000; Path=/; HttpOnly

{"message": "Login successful", "session_id": "123e4567-e89b-12d3... "}
```
*(Nếu thất bại với user không tồn tại hoặc sai pass, HTTP/1.1 sẽ trả về Status Code `401 Unauthorized` và `"error": "Invalid username or password"`).*

**4. Khởi chạy Hệ Thống Proxy & P2P (Giai đoạn 3, 4, 5, 6)**

Để giáo viên chấm điểm toàn bộ hệ thống P2P bao gồm UI và Proxy, làm theo các bước sau:
1. Mở Terminal thứ nhất, khởi chạy Proxy Server hỗ trợ Load-Balancing và Forwarding:
   `python start_proxy.py --server-ip 127.0.0.1 --server-port 8080`
2. Mở Terminal thứ 2, khởi chạy Node mạng P2P cho User 1 (đóng vai trò Tracker + Node 1):
   `python start_sampleapp.py --server-ip 127.0.0.1 --server-port 2026`
3. Mở Terminal thứ 3, khởi chạy Node mạng P2P cho User 2 (Node 2):
   `python start_sampleapp.py --server-ip 127.0.0.1 --server-port 2027`
4. Mở 2 Tab trình duyệt, truy cập `www/login.html` dưới dạng local file (`file:///.../www/login.html`).
   - Tab 1: Đăng nhập với `user1` ở port `2026`.
   - Tab 2: Đăng nhập với `user2` ở port `2027`.
5. Bạn sẽ được chuyển sang giao diện `index.html`. Hai bên ứng dụng sẽ tự động đồng bộ hoá danh bạ (dùng Tracker API GĐ 3) qua background polling. Bạn có thể chat P2P mượt mà thông qua giao thức HTTP (GĐ 4). Nước cờ Non-blocking Coroutines (GĐ 1) đảo bảo server không bao giờ bị nghẽn!

*(Lưu ý: Proxy đã được configure trong `config/proxy.conf` trỏ `127.0.0.1:8080` tới `127.0.0.1:2026`. Bạn cũng có thể mở Proxy bằng lệnh `curl -v http://127.0.0.1:8080/get-list` để thấy Reverse Proxy hoạt động.)*

## License

This project is licensed under the MIT License Agreement, intended primarily for educational purposes of studying while attending the specified course.


## File Structure

```
├── apps
│   ├── __init__.py
│   └── sampleapp.py
├── cert
├── config
│   └── proxy.conf
├── daemon
│   ├── __init__.py
│   ├── asynaprous.py
│   ├── backend.py
│   ├── dictionary.py
│   ├── httpadapter.py
│   ├── proxy.py
│   ├── request.py
│   ├── response.py
│   └── utils.py
├── db
├── static
│   ├── css
│   │   └── styles.css
│   ├── images
│   │   ├── favicon.ico
│   │   ├── welcome.jpg
│   │   └── welcome.png
│   └── js
├── www
│   ├── form.html
│   ├── index.html
│   └── login.html
├── README.md
├── __init__.py
├── start_backend.py
├── start_proxy.py
└── start_sampleapp.py
```
