import urllib.request
import json
import time
import subprocess
import os

print("Starting server...")
proc = subprocess.Popen(["python", "start_sampleapp.py", "--server-ip", "127.0.0.1", "--server-port", "2026"])
time.sleep(2) # Give server time to start

try:
    print("\n--- 1. Testing Login ---")
    req = urllib.request.Request("http://127.0.0.1:2026/login", data=json.dumps({"username": "user1", "password": "pass1"}).encode('utf-8'), method="POST")
    req.add_header("Content-Type", "application/json")
    res = urllib.request.urlopen(req)
    # Get cookie
    cookies_header = res.getheader('Set-Cookie')
    print("Login Response Code:", res.getcode())
    print("Set-Cookie Header:", cookies_header)
    print("Response Body:", res.read().decode())
    
    session = cookies_header.split(";")[0]

    print("\n--- 2. Testing Tracker Submit ---")
    req2 = urllib.request.Request("http://127.0.0.1:2026/submit-info", data=json.dumps({"ip": "1.2.3.4", "port": 5050}).encode('utf-8'), method="POST")
    req2.add_header("Cookie", session)
    res2 = urllib.request.urlopen(req2)
    print("Submit Response Code:", res2.getcode())
    print("Response Body:", res2.read().decode())

    print("\n--- 3. Testing Tracker Get List ---")
    req3 = urllib.request.Request("http://127.0.0.1:2026/get-list", method="GET")
    req3.add_header("Cookie", session)
    res3 = urllib.request.urlopen(req3)
    print("Get List Response Code:", res3.getcode())
    print("Response Body:", res3.read().decode())
    
finally:
    proc.kill()
    print("Server killed.")
