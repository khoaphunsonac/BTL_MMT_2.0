import urllib.request
import json
import time
import subprocess

print("Starting Node 1 (Tracker + user1) on 2026...")
p1 = subprocess.Popen(["python", "start_sampleapp.py", "--server-ip", "127.0.0.1", "--server-port", "2026"])
print("Starting Node 2 (user2) on 2027...")
p2 = subprocess.Popen(["python", "start_sampleapp.py", "--server-ip", "127.0.0.1", "--server-port", "2027"])

time.sleep(3)

try:
    print("\n--- 1. Login user1 (Node 1) ---")
    req1 = urllib.request.Request("http://127.0.0.1:2026/login", data=json.dumps({"username": "user1", "password": "pass1"}).encode('utf-8'), method="POST")
    res1 = urllib.request.urlopen(req1)
    s1 = res1.getheader('Set-Cookie').split(";")[0]

    print("\n--- 2. Login user2 (Node 2) ---")
    req2 = urllib.request.Request("http://127.0.0.1:2027/login", data=json.dumps({"username": "user2", "password": "pass2"}).encode('utf-8'), method="POST")
    res2 = urllib.request.urlopen(req2)
    s2 = res2.getheader('Set-Cookie').split(";")[0]
    
    print("\n--- 3. Tracker: Node 2 announces itself to Node 1 ---")
    # Actually wait, Node 1 is tracking everyone, so Node 1 needs to know Node 2 IP.
    # To bypass Tracker UI logic, let's just make Node 1 submit user2 to Node 1's PEERS? 
    # No, ONLY user2 can submit itself. 
    # But user2 doesn't have a session on Node 1! Ah! user2 logs into Node 1 to get session, then submits.
    req_trk_login = urllib.request.Request("http://127.0.0.1:2026/login", data=json.dumps({"username": "user2", "password": "pass2"}).encode('utf-8'), method="POST")
    res_trk = urllib.request.urlopen(req_trk_login)
    s_trk = res_trk.getheader('Set-Cookie').split(";")[0]

    req3 = urllib.request.Request("http://127.0.0.1:2026/submit-info", data=json.dumps({"ip": "127.0.0.1", "port": 2027}).encode('utf-8'), method="POST")
    req3.add_header("Cookie", s_trk)
    urllib.request.urlopen(req3)
    
    print("\n--- 4. P2P: Node 1 sends message to Node 2 ---")
    # Node 1 sends via browser simulator (using s1 cookie)
    req4 = urllib.request.Request("http://127.0.0.1:2026/send-peer", data=json.dumps({
        "type": "outbound",
        "target": "user2",
        "message": "Hello from Node 1 via HTTP P2P!"
    }).encode('utf-8'), method="POST")
    req4.add_header("Cookie", s1)
    res4 = urllib.request.urlopen(req4)
    print("Send-peer response:", res4.read().decode())
    
    time.sleep(1)
    
    print("\n--- 5. Verify: Node 2 Chat History ---")
    req5 = urllib.request.Request("http://127.0.0.1:2027/get-messages", method="GET")
    req5.add_header("Cookie", s2)
    res5 = urllib.request.urlopen(req5)
    print("Messages on Node 2:", res5.read().decode())

finally:
    p1.kill()
    p2.kill()
    print("Servers killed.")

