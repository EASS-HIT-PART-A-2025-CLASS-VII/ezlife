import requests
import time

def test_user_create():
    timestamp = int(time.time())
    user_data = {
        "username": f"cruduser_{timestamp}",
        "email": f"crud_{timestamp}@example.com",
        "password": "testpass123"
    }
    response = requests.post("http://localhost:8001/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    print("✅ User CREATE working")

def test_user_read():
    timestamp = int(time.time())
    user_data = {
        "username": f"cruduser_{timestamp}",
        "email": f"crud_{timestamp}@example.com",
        "password": "testpass123"
    }
    requests.post("http://localhost:8001/register", json=user_data)
    
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    token_response = requests.post("http://localhost:8001/token", data=login_data)
    
    if token_response.status_code == 200:
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        profile_response = requests.get("http://localhost:8001/profile", headers=headers)
        assert profile_response.status_code == 200
        print("✅ User READ working")

def test_user_update():
    timestamp = int(time.time())
    user_data = {
        "username": f"cruduser_{timestamp}",
        "email": f"crud_{timestamp}@example.com",
        "password": "testpass123"
    }
    requests.post("http://localhost:8001/register", json=user_data)
    
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    token_response = requests.post("http://localhost:8001/token", data=login_data)
    
    if token_response.status_code == 200:
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {"email": f"updated_{int(time.time())}@example.com"}
        response = requests.put("http://localhost:8001/profile", json=update_data, headers=headers)
        assert response.status_code in [200, 204]
        print("✅ User UPDATE working")

def test_user_delete():
    timestamp = int(time.time())
    user_data = {
        "username": f"cruduser_{timestamp}",
        "email": f"crud_{timestamp}@example.com",
        "password": "testpass123"
    }
    requests.post("http://localhost:8001/register", json=user_data)
    
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    token_response = requests.post("http://localhost:8001/token", data=login_data)
    
    if token_response.status_code == 200:
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.delete("http://localhost:8001/profile", headers=headers)
        assert response.status_code in [200, 204]
        print("✅ User DELETE working")
