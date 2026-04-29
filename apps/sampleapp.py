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
import time

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


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Max-Age": "86400"
    }


def json_headers(extra=None):
    headers = {"Content-Type": "application/json"}
    if extra:
        headers.update(extra)
    headers.update(cors_headers())
    return headers


def extract_session_id(headers):
    """Extract session token from Authorization or Cookie headers."""
    auth_header = headers.get('authorization', '')
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]

    cookie_header = headers.get('cookie', '')
    for item in cookie_header.split(';'):
        if '=' in item:
            k, v = item.strip().split('=', 1)
            if k == "session_id":
                return v
    return None

def check_auth(headers):
    """
    Helper function để kiểm tra xem cookie/session_id có hợp lệ không.
    """
    session_id = extract_session_id(headers)
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
            return (json_str.encode("utf-8"), json_headers(custom_headers))
        else:
            # Login thất bại
            data = {"error": "Invalid username or password"}
            return (json.dumps(data).encode("utf-8"), json_headers({"Status": "401 Unauthorized"}))
            
    except Exception as e:
        data = {"error": str(e)}
        return (json.dumps(data).encode("utf-8"), json_headers({"Status": "400 Bad Request"}))


@app.route('/login', methods=['OPTIONS'])
def login_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))

@app.route("/echo", methods=["POST"])
def echo(headers="guest", body="anonymous"):
    print("[SampleApp] received body {}".format(body))

    try:
        message = json.loads(body)
        data = {"received": message }
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"), json_headers())
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON"}
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"), json_headers({"Status": "400 Bad Request"}))


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
    return (json_str.encode("utf-8"), json_headers())

# ==========================================
# PHASE 3: TRACKER SERVER
# ==========================================

PEERS = {}
PEER_TIMEOUT_SECONDS = 12


def upsert_peer(username, ip=None, port=None, online=True):
    peer = PEERS.get(username, {})
    if ip is not None:
        peer["ip"] = ip
    if port is not None:
        peer["port"] = port
    peer["online"] = online
    peer["last_seen"] = int(time.time())
    PEERS[username] = peer


def mark_peer_offline(username):
    if username not in PEERS:
        return
    PEERS[username]["online"] = False
    PEERS[username]["last_seen"] = int(time.time())

@app.route('/submit-info', methods=['POST'])
def submit_info(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), json_headers({"Status": "401 Unauthorized"}))
    
    try:
        payload = json.loads(body)
        ip = payload.get("ip")
        port = payload.get("port")
        if ip and port:
            upsert_peer(username, ip, port, online=True)
            return (json.dumps({"message": "Info submitted successfully", "peers": PEERS}).encode("utf-8"), json_headers())
        return (json.dumps({"error": "Missing ip or port"}).encode("utf-8"), json_headers({"Status": "400 Bad Request"}))
    except Exception as e:
        return (json.dumps({"error": "Invalid format"}).encode("utf-8"), json_headers({"Status": "400 Bad Request"}))


@app.route('/submit-info', methods=['OPTIONS'])
def submit_info_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))


@app.route('/heartbeat', methods=['POST'])
def heartbeat(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), json_headers({"Status": "401 Unauthorized"}))

    try:
        payload = json.loads(body) if isinstance(body, str) and body.strip() else {}
    except Exception:
        payload = {}

    ip = payload.get("ip")
    port = payload.get("port")
    upsert_peer(username, ip, port, online=True)
    return (json.dumps({"status": "ok"}).encode("utf-8"), json_headers())


@app.route('/heartbeat', methods=['OPTIONS'])
def heartbeat_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))


@app.route('/logout', methods=['POST'])
def logout(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), json_headers({"Status": "401 Unauthorized"}))

    session_id = extract_session_id(headers)
    if session_id in SESSIONS:
        del SESSIONS[session_id]

    mark_peer_offline(username)
    return (json.dumps({"message": "Logged out"}).encode("utf-8"), json_headers())


@app.route('/logout', methods=['OPTIONS'])
def logout_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))

@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), json_headers({"Status": "401 Unauthorized"}))
    
    now = int(time.time())
    for uname, info in PEERS.items():
        if info.get("online") and (now - info.get("last_seen", now) > PEER_TIMEOUT_SECONDS):
            info["online"] = False

    return (json.dumps({"peers": PEERS}).encode("utf-8"), json_headers())


@app.route('/get-list', methods=['OPTIONS'])
def get_list_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))

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
            return (json.dumps({"status": "accepted", "message": f"Hello {peer_username}"}).encode("utf-8"), json_headers())
        return (json.dumps({"error": "Missing username"}).encode("utf-8"), json_headers({"Status": "400 Bad Request"}))
    except:
        return (json.dumps({"error": "Invalid JSON mapping"}).encode("utf-8"), json_headers({"Status": "400 Bad Request"}))


@app.route('/connect-peer', methods=['OPTIONS'])
def connect_peer_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))

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
            return (json.dumps({"status": "delivered"}).encode("utf-8"), json_headers())
        
        # Gửi tin nhắn đi (OUTBOUND) từ Trình duyệt User -> Gọi sang Peer khác
        elif req_type == "outbound":
            username = check_auth(headers)
            if not username:
                return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), json_headers({"Status": "401 Unauthorized"}))
            
            target_user = payload.get("target")
            msg = payload.get("message")
            
            # Ưu tiên lấy IP/Port từ Payload (do UI lấy từ Tracker gửi lên)
            target_ip = payload.get("target_ip")
            target_port = payload.get("target_port")

            # Tra cứu IP/Port từ PEERS đã lưu (Fallback)
            if not target_ip or not target_port:
                if target_user not in PEERS:
                    return (json.dumps({"error": "Target user not found"}).encode("utf-8"), json_headers({"Status": "404 Not Found"}))
                if not PEERS[target_user].get("online", False):
                    return (json.dumps({"error": "Target user is offline"}).encode("utf-8"), json_headers({"Status": "409 Conflict"}))
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
                    return (json.dumps({"status": "sent to peer"}).encode("utf-8"), json_headers())
            except urllib.error.URLError as e:
                mark_peer_offline(target_user)
                return (json.dumps({"error": f"Failed reaching peer: {str(e)}"}).encode("utf-8"), json_headers({"Status": "503 Service Unavailable"}))
                
        return (json.dumps({"error": "Invalid internal format"}).encode("utf-8"), json_headers({"Status": "400 Bad Request"}))
    except Exception as e:
        return (json.dumps({"error": str(e)}).encode("utf-8"), json_headers({"Status": "400 Bad Request"}))


@app.route('/send-peer', methods=['OPTIONS'])
def send_peer_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))

@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), json_headers({"Status": "401 Unauthorized"}))
    
    try:
        payload = json.loads(body)
        msg = payload.get("message")
        ui_peers = payload.get("peers")
        success_count = 0
        
        peers_to_use = ui_peers if ui_peers else PEERS

        for peer_uname, peer_info in peers_to_use.items():
            if peer_uname == username:
                continue # Không gửi cho chính mình
            if not peer_info.get("online", False):
                continue
                
            try:
                url = f"http://{peer_info['ip']}:{peer_info['port']}/send-peer"
                outbound_data = json.dumps({"type": "inbound", "from": username, "message": msg}).encode("utf-8")
                req = urllib.request.Request(url, data=outbound_data, method="POST")
                req.add_header("Content-Type", "application/json")
                
                res = urllib.request.urlopen(req, timeout=1)
                if res.getcode() == 200:
                    success_count += 1
            except:
                mark_peer_offline(peer_uname)
                pass # Bỏ qua peer bị offline
                
        CHAT_HISTORY.append({"from": username, "to": "ALL", "message": msg, "type": "broadcast_sent"})
        return (json.dumps({"status": "broadcasted", "success_peers": success_count}).encode("utf-8"), json_headers())
    except Exception as e:
        return (json.dumps({"error": str(e)}).encode("utf-8"), json_headers({"Status": "400 Bad Request"}))


@app.route('/broadcast-peer', methods=['OPTIONS'])
def broadcast_peer_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))

@app.route('/get-messages', methods=['GET'])
def get_messages(headers, body):
    username = check_auth(headers)
    if not username:
        return (json.dumps({"error": "Unauthorized"}).encode("utf-8"), json_headers({"Status": "401 Unauthorized"}))
    
    return (json.dumps({"history": CHAT_HISTORY}).encode("utf-8"), json_headers())


@app.route('/get-messages', methods=['OPTIONS'])
def get_messages_options(headers, body):
    return (b"", json_headers({"Status": "204 No Content"}))

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
    except Exception as e:
        print("ERROR loading app.js:", e)
        return (b"404 Not Found", {"Status": "404 Not Found"})

def create_sampleapp(ip, port):
    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()

