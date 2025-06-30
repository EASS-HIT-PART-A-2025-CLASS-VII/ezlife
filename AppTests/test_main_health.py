import requests

def test_main_backend_health():
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Main Backend is healthy")

def test_task_service_health():
    response = requests.get("http://localhost:8002/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Task Estimation Service is healthy")
