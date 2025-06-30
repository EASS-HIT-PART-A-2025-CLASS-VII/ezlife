import requests

def test_task_create():
    task_data = {
        "description": "CRUD test task",
        "due_date": "2025-07-15T10:00:00",
        "completed": False
    }
    response = requests.post("http://localhost:8000/tasks", json=task_data)
    assert response.status_code in [200, 201]
    data = response.json()
    assert "description" in data
    print("✅ Task CREATE working")
    return data.get("id") or data.get("_id")

def test_task_read():
    task_id = test_task_create()
    if task_id:
        response = requests.get(f"http://localhost:8000/tasks/{task_id}")
        assert response.status_code == 200
        print("✅ Task READ working")

def test_task_update():
    task_id = test_task_create()
    if task_id:
        update_data = {
            "description": "Updated CRUD test task",
            "completed": True
        }
        response = requests.put(f"http://localhost:8000/tasks/{task_id}", json=update_data)
        assert response.status_code in [200, 204]
        print("✅ Task UPDATE working")

def test_task_delete():
    task_id = test_task_create()
    if task_id:
        response = requests.delete(f"http://localhost:8000/tasks/{task_id}")
        assert response.status_code in [200, 204]
        print("✅ Task DELETE working")

def test_task_list():
    response = requests.get("http://localhost:8000/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print("✅ Task LIST working")

def test_activity_create():
    activity_data = {
        "name": "CRUD Test Activity",
        "date": "2025-07-01",
        "completed": False
    }
    response = requests.post("http://localhost:8000/activities", json=activity_data)
    assert response.status_code in [200, 201]
    data = response.json()
    assert "name" in data
    print("✅ Activity CREATE working")
    return data.get("id") or data.get("_id")

def test_activity_read():
    activity_id = test_activity_create()
    if activity_id:
        response = requests.get(f"http://localhost:8000/activities/{activity_id}")
        assert response.status_code == 200
        print("✅ Activity READ working")

def test_activity_update():
    activity_id = test_activity_create()
    if activity_id:
        update_data = {
            "name": "Updated CRUD Test Activity",
            "completed": True
        }
        response = requests.put(f"http://localhost:8000/activities/{activity_id}", json=update_data)
        assert response.status_code in [200, 204]
        print("✅ Activity UPDATE working")

def test_activity_delete():
    activity_id = test_activity_create()
    if activity_id:
        response = requests.delete(f"http://localhost:8000/activities/{activity_id}")
        assert response.status_code in [200, 204]
        print("✅ Activity DELETE working")

def test_activity_list():
    response = requests.get("http://localhost:8000/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print("✅ Activity LIST working")
    assert response.status_code in [200, 201]
    data = response.json()
    assert "name" in data
    print("✅ Activity creation working")
