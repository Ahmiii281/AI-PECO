import urllib.request
import json

data = json.dumps({"name": "Demo Admin", "email": "admin@aipeco.com", "password": "admin123"}).encode('utf-8')
req = urllib.request.Request("http://localhost:8000/api/auth/register", data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as f:
        print("Reg:", f.read().decode('utf-8'))
except Exception as e:
    print("Reg err:", e)

data = json.dumps({"email": "admin@aipeco.com", "password": "admin123"}).encode('utf-8')
req = urllib.request.Request("http://localhost:8000/api/auth/login", data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as f:
        print("Login:", f.read().decode('utf-8'))
except Exception as e:
    print("Login err:", e)
