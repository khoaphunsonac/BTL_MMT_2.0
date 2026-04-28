# Phân tích Yêu cầu Đồ án (BTL 1)

Đồ án yêu cầu xây dựng một HTTP server sử dụng cơ chế non-blocking và một ứng dụng chat lai (hybrid) kết hợp cả mô hình Client-Server và Peer-to-Peer (P2P).

## Các ràng buộc kỹ thuật cốt lõi:
* **Không dùng thư viện ngoài:** Backend bắt buộc phải sử dụng thư viện chuẩn của Python (như `socket`, `asyncio`, `threading`). Tuyệt đối không dùng các web framework có sẵn.
* **Sử dụng AsynapRous:** Phải phát triển dựa trên framework AsynapRous đã được cung cấp trong mã nguồn.
* **Cơ chế Non-blocking:** Giao tiếp mạng phải là non-blocking. Bạn có thể chọn một trong ba hướng: Multi-thread, Event-driven/Callback, hoặc Coroutine (async/await).
* **Giới hạn Front-end:** JavaScript chỉ được phép sử dụng ở phía client (trình duyệt) để cập nhật giao diện hoặc gọi API bất đồng bộ.

## Các tính năng cốt lõi cần hiện thực:
* **Authentication (Xác thực):** Phải có tính năng đăng nhập sử dụng HTTP Headers hoặc Cookies. Theo như bạn định hướng, hệ thống không cần database mà chỉ cần hardcode khoảng 3 user với username/password cụ thể là đủ.
* **Mô hình Client-Server (Tracker):** Server đóng vai trò trung tâm lưu trữ danh sách các peer đang hoạt động (IP và Port). Các peer mới tham gia sẽ truy vấn server để lấy danh sách này.
* **Mô hình P2P (Chat):** Sau khi có IP/Port từ Tracker, các peer tự thiết lập kết nối trực tiếp với nhau để gửi/nhận tin nhắn (direct) hoặc gửi cho toàn bộ nhóm (broadcast) mà không đi qua server.

---


### Giai đoạn 1: Core Server & Non-blocking 
- [x] Đọc hiểu mã nguồn của AsynapRous, đặc biệt là các file `daemon/asynaprous.py`, `daemon/backend.py` và `start_backend.py`.
- [x] Lựa chọn và tích hợp cơ chế non-blocking cho HTTP server. Cần đảm bảo hàm `recv()` và `send()` không làm treo luồng chính.
- [x] Thiết lập module routing để server có thể nhận diện và xử lý các RESTful API method (`GET`, `POST`, `PUT`, `DELETE`).

### Giai đoạn 2: Authentication & User Management 
- [x] Định nghĩa sẵn 3 user (ví dụ: user1, user2, user3 kèm password) trong một dictionary Python.
- [x] Viết handler cho API `/login/` sử dụng phương thức `POST` hoặc `PUT`.
- [x] Cấu hình server trả về `Set-Cookie` khi đăng nhập thành công và viết logic kiểm tra cookie hợp lệ cho các request tiếp theo.

### Giai đoạn 3: Xây dựng Tracker Server 
- [x] Xây dựng API `/submit-info/` để các client báo cáo IP và Port của họ khi vừa đăng nhập thành công.
- [x] Lưu trữ danh sách peer này vào bộ nhớ tạm (ví dụ: một mảng hoặc dictionary toàn cục).
- [x] Xây dựng API `/get-list/` để trả về danh sách các peer đang active dưới định dạng JSON để client gọi về.

### Giai đoạn 4: Giao tiếp P2P - Peer Communication 
- [x] Viết script chạy ẩn ở phía client (hoặc một daemon thread nhỏ) để lắng nghe kết nối từ các peer khác.
- [x] Định nghĩa API `/connect-peer/` để thiết lập bắt tay ban đầu giữa hai client.
- [x] Hiện thực API `/send-peer/` (chat 1-1) và `/broadcast-peer/` (gửi tin cho tất cả peer trong danh sách). Đảm bảo tin nhắn được xử lý mượt mà, không gián đoạn.

### Giai đoạn 5: Thiết kế Client UI 
- [x] Tạo các file tĩnh `login.html`, `index.html` và đặt vào thư mục `www/`. Các file CSS/JS bỏ vào thư mục `static/`.
- [x] Code JavaScript sử dụng fetch API để gọi `/login/` và lấy danh sách peer qua `/get-list/`.
- [x] Dựng giao diện HTML đơn giản: Cần có danh sách channel/peer bên trái, và một cửa sổ tin nhắn cuộn được (scrollable) bên phải.
- [x] Bắt sự kiện người dùng nhập text và nhấn Submit, sau đó gọi trực tiếp API `/send-peer/` hoặc `/broadcast-peer/`.

### Giai đoạn 6: Tích hợp, Test & Báo cáo 
- [x] Chạy `start_proxy.py` và `start_sampleapp.py` để đảm bảo hệ thống proxy và backend hoạt động trơn tru với nhau.
- [x] Mở nhiều tab ẩn danh (Incognito) hoặc nhiều trình duyệt khác nhau để test tính đồng thời (concurrency) và xác thực Cookie.
- [x] Chuẩn bị kịch bản demo (chiếm 7 điểm) và viết báo cáo (chiếm 3 điểm).
- [x] Gom code và báo cáo nén thành file `assignment_STUDENTID.zip` để nộp lên LMS.

Lưu ý khi hoàn thành mỗi giai đoạn, hãy thực hiện vòng test đến khi thành công rồi mới chuyển sang giai đoạn tiếp theo.
