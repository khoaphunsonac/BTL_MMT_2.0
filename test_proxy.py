import urllib.request
import json
import time
import subprocess

print("Starting Backend on 2026...")
p_backend = subprocess.Popen(["python", "start_sampleapp.py", "--server-ip", "127.0.0.1", "--server-port", "2026"])

print("Starting Proxy on 8080...")
p_proxy = subprocess.Popen(["python", "start_proxy.py", "--server-ip", "127.0.0.1", "--server-port", "8080"])

time.sleep(3)

try:
    print("\n--- Testing Proxy Routing ---")
    req = urllib.request.Request("http://127.0.0.1:8080/login", data=json.dumps({"username": "user1", "password": "pass1"}).encode('utf-8'), method="POST")
    req.add_header("Host", "127.0.0.1:8080")
    res = urllib.request.urlopen(req)
    print("Response Code:", res.getcode())
    print("Response Body:", res.read().decode())
    
except Exception as e:
    print("Error:", str(e))
    
finally:
    p_backend.kill()
    p_proxy.kill()
    print("Servers killed.")

