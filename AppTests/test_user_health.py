import requests

def test_user_service_health():
    response = requests.get("http://localhost:8001/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ User Service is healthy")
