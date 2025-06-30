import requests

def test_file_service_health():
    response = requests.get("http://localhost:8003/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ File Service is healthy")
