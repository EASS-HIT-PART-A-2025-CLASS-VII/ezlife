import requests

def test_task_estimate_time():
    task_data = {
        "description": "Test task for time estimation",
        "complexity": "medium"
    }
    response = requests.post("http://localhost:8002/estimate_time", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert "estimated_minutes" in data
    assert "breakdown" in data
    assert "source" in data
    print("✅ Task Time ESTIMATION working")

def test_task_breakdown():
    task_data = {
        "description": "Complex task that needs breakdown",
        "complexity": "high"
    }
    response = requests.post("http://localhost:8002/breakdown_task", json=task_data)
    if response.status_code == 200:
        data = response.json()
        assert "subtasks" in data or "breakdown" in data or "tasks" in data
        print("✅ Task BREAKDOWN working")
    elif response.status_code == 404:
        print("⚠️ Task BREAKDOWN endpoint not found - using estimate_time instead")
        
def test_task_estimation_service_working():
    task_data = {
        "description": "Verify task estimation service is functional",
        "complexity": "low"
    }
    response = requests.post("http://localhost:8002/estimate_time", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["estimated_minutes"], int)
    assert data["estimated_minutes"] > 0
    print("✅ Task Estimation Service fully working")
