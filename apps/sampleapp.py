#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
app.sampleapp
~~~~~~~~~~~~~~~~~

"""

import sys
import os
import urllib.request
import urllib.error
import importlib.util
import json
import uuid

from daemon import AsynapRous

app = AsynapRous()

# Mock Database cho yêu cầu Giai đoạn 2
USERS = {
    "user1": "pass1",
    "user2": "pass2",
    "user3": "pass3"
}

# Lưu trữ Session ID đang hoạt động
SESSIONS = {}

def check_auth(headers):
    """
    Helper function để kiểm tra xem cookie/session_id có hợp lệ không.
    """
    # Trích xuất bearer token từ Authorization (cho UI Frontend)
    auth_header = headers.get('authorization', '')
    if auth_header.startswith("Bearer "):
        session_id = auth_header.split(" ")[1]
        if session_id in SESSIONS:
            return SESSIONS[session_id]
                
    # Fallback trích xuất từ Cookie
    cookie_header = headers.get('cookie', '')
    cookies = {}
    for item in cookie_header.split(';'):
        if '=' in item:
            k, v = item.strip().split('=', 1)
            cookies[k] = v
            
    session_id = cookies.get('session_id')
    if session_id and session_id in SESSIONS:
        return SESSIONS[session_id]
    return None

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.
    Xác thực user và trả về Set-Cookie nếu thành công.
    """
    print("[SampleApp] Logging in {} to {}".format(headers, body))
    
    try:
        # Xử lý parse JSON body
        if isinstance(body, dict):
            payload = body
        elif isinstance(body, str) and body.strip() != "":
            payload = json.loads(body)
        else:
            payload = {}

        username = payload.get("username")
        password = payload.get("password")

        if username in USERS and USERS[username] == password:
            # Login thành công
            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = username
            
            data = {"message": "Login successful", "session_id": session_id}
            json_str = json.dumps(data)
            
            # Trả về payload json chung với thông tin custom header điều khiển Set-Cookie
            custom_headers = {
                "Set-Cookie": f"session_id={session_id}; Path=/; HttpOnly"
            }
            # Trả về tuple thay vì chỉ nội dung, để daemon/httpadapter có thể đọc được headers
            return (json_str.encode("utf-8"), custom_headers)
        else:
            # Login thất bại
            data = {"error": "Invalid username or password"}
            return (json.dumps(data).encode("utf-8"), {"Status": "401 Unauthorized"})
            
    except Exception as e:
        data = {"error": str(e)}
        return (json.dumps(data).encode("utf-8"), {"Status": "400 Bad Request"})

@app.route("/echo", methods=["POST"])
def echo(headers="guest", body="anonymous"):
    print("[SampleApp] received body {}".format(body))

    try:
        message = json.loads(body)
        data = {"received": message }
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON"}
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))


@app.route('/hello', methods=['PUT'])
async def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] **ASYNC** Hello in {} to {}".format(headers, body))
    data =  {"id": 1, "name": "Alice", "email": "alice@example.com"}

    # Convert to JSON string
    json_str = json.dumps(data)
    return (json_str.encode("utf-8"))

# ==========================================
# PHASE 3: TRACKER SERVER
# ==========================================

PEERS = {}

@app.route('/submit-info', methods=['POST'])
def submit_info(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), {"Status": "401 Unauthorized", "Content-Type": "application/json"})
    
    try:
        payload = json.loads(body)
        ip = payload.get("ip")
        port = payload.get("port")
        if ip and port:
            PEERS[username] = {"ip": ip, "port": port}
            return (json.dumps({"message": "Info submitted successfully", "peers": PEERS}).encode("utf-8"), {"Content-Type": "application/json"})
        return (json.dumps({"error": "Missing ip or port"}).encode("utf-8"), {"Status": "400 Bad Request", "Content-Type": "application/json"})
    except Exception as e:
        return (json.dumps({"error": "Invalid format"}).encode("utf-8"), {"Status": "400 Bad Request", "Content-Type": "application/json"})

@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), {"Status": "401 Unauthorized", "Content-Type": "application/json"})
    
    return (json.dumps({"peers": PEERS}).encode("utf-8"), {"Content-Type": "application/json"})

# ==========================================
# PHASE 4: P2P COMMUNICATION
# ==========================================

ACTIVE_CONNECTIONS = set()
CHAT_HISTORY = []

@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers, body):
    # API nhận Ping bắt tay từ Peer khác
    try:
        payload = json.loads(body)
        peer_username = payload.get("username")
        if peer_username:
            ACTIVE_CONNECTIONS.add(peer_username)
            return (json.dumps({"status": "accepted", "message": f"Hello {peer_username}"}).encode("utf-8"), {"Content-Type": "application/json"})
        return (json.dumps({"error": "Missing username"}).encode("utf-8"), {"Status": "400 Bad Request", "Content-Type": "application/json"})
    except:
        return (json.dumps({"error": "Invalid JSON mapping"}).encode("utf-8"), {"Status": "400 Bad Request", "Content-Type": "application/json"})

@app.route('/send-peer', methods=['POST'])
def send_peer(headers, body):
    try:
        payload = json.loads(body)
        req_type = payload.get("type", "inbound")
        
        # Nhận tin nhắn từ Peer (INBOUND)
        if req_type == "inbound":
            from_user = payload.get("from")
            msg = payload.get("message")
            CHAT_HISTORY.append({"from": from_user, "message": msg, "type": "direct"})
            return (json.dumps({"status": "delivered"}).encode("utf-8"), {"Content-Type": "application/json"})
        
        # Gửi tin nhắn đi (OUTBOUND) từ Trình duyệt User -> Gọi sang Peer khác
        elif req_type == "outbound":
            username = check_auth(headers)
            if not username:
                return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), {"Status": "401 Unauthorized", "Content-Type": "application/json"})
            
            target_user = payload.get("target")
            msg = payload.get("message")
            
            # Tra cứu IP/Port từ PEERS đã lưu
            if target_user not in PEERS:
                return (json.dumps({"error": "Target user not found"}).encode("utf-8"), {"Status": "404 Not Found", "Content-Type": "application/json"})
            
            target_ip = PEERS[target_user]["ip"]
            target_port = PEERS[target_user]["port"]
            
            # Bắn HTTP PPOST tới đích
            url = f"http://{target_ip}:{target_port}/send-peer"
            outbound_data = json.dumps({"type": "inbound", "from": username, "message": msg}).encode("utf-8")
            
            req = urllib.request.Request(url, data=outbound_data, method="POST")
            req.add_header("Content-Type", "application/json")
            
            try:
                res = urllib.request.urlopen(req, timeout=3)
                if res.getcode() == 200:
                    CHAT_HISTORY.append({"from": username, "to": target_user, "message": msg, "type": "direct_sent"})
                    return (json.dumps({"status": "sent to peer"}).encode("utf-8"), {"Content-Type": "application/json"})
            except urllib.error.URLError as e:
                return (json.dumps({"error": f"Failed reaching peer: {str(e)}"}).encode("utf-8"), {"Status": "503 Service Unavailable", "Content-Type": "application/json"})
                
        return (json.dumps({"error": "Invalid internal format"}).encode("utf-8"), {"Status": "400 Bad Request", "Content-Type": "application/json"})
    except Exception as e:
        return (json.dumps({"error": str(e)}).encode("utf-8"), {"Status": "400 Bad Request", "Content-Type": "application/json"})

@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), {"Status": "401 Unauthorized", "Content-Type": "application/json"})
    
    try:
        payload = json.loads(body)
        msg = payload.get("message")
        success_count = 0
        
        for peer_uname, peer_info in PEERS.items():
            if peer_uname == username:
                continue # Không gửi cho chính mình
                
            try:
                url = f"http://{peer_info['ip']}:{peer_info['port']}/send-peer"
                outbound_data = json.dumps({"type": "inbound", "from": username, "message": msg}).encode("utf-8")
                req = urllib.request.Request(url, data=outbound_data, method="POST")
                req.add_header("Content-Type", "application/json")
                
                res = urllib.request.urlopen(req, timeout=1)
                if res.getcode() == 200:
                    success_count += 1
            except:
                pass # Bỏ qua peer bị offline
                
        CHAT_HISTORY.append({"from": username, "to": "ALL", "message": msg, "type": "broadcast_sent"})
        return (json.dumps({"status": "broadcasted", "success_peers": success_count}).encode("utf-8"), {"Content-Type": "application/json"})
    except Exception as e:
        return (json.dumps({"error": str(e)}).encode("utf-8"), {"Status": "400 Bad Request", "Content-Type": "application/json"})

@app.route('/get-messages', methods=['GET'])
def get_messages(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), {"Status": "401 Unauthorized", "Content-Type": "application/json"})
    
    return (json.dumps({"history": CHAT_HISTORY}).encode("utf-8"), {"Content-Type": "application/json"})

# ==========================================
# GIAI ĐOẠN 5: FRONTEND STATIC ROUTES
# ==========================================
@app.route('/login.html', methods=['GET'])
def serve_login(headers, body):
    try:
        with open("www/login.html", "r", encoding="utf-8") as f:
            return (f.read().encode("utf-8"), {"Content-Type": "text/html"})
    except:
        return (b"404 Not Found", {"Status": "404 Not Found"})

@app.route('/index.html', methods=['GET'])
def serve_index(headers, body):
    try:
        with open("www/index.html", "r", encoding="utf-8") as f:
            return (f.read().encode("utf-8"), {"Content-Type": "text/html"})
    except:
        return (b"404 Not Found", {"Status": "404 Not Found"})

@app.route('/static/css/styles.css', methods=['GET'])
def serve_css(headers, body):
    try:
        with open("static/css/styles.css", "r", encoding="utf-8") as f:
            return (f.read().encode("utf-8"), {"Content-Type": "text/css"})
    except:
        return (b"404 Not Found", {"Status": "404 Not Found"})

@app.route('/static/js/app.js', methods=['GET'])
def serve_js(headers, body):
    try:
        with open("static/js/app.js", "r", encoding="utf-8") as f:
            return (f.read().encode("utf-8"), {"Content-Type": "application/javascript"})
    except:
        return (b"404 Not Found", {"Status": "404 Not Found"})

def create_sampleapp(ip, port):
    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()

