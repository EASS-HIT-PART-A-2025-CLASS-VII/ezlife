import requests
import io

def test_file_create():
    file_content = b"Test file content for CRUD"
    files = {"file": ("test_crud.txt", io.BytesIO(file_content), "text/plain")}
    data = {"description": "CRUD test file", "user_id": "crud_test_user"}
    
    response = requests.post("http://localhost:8003/upload", files=files, data=data)
    assert response.status_code == 200
    response_data = response.json()
    assert "_id" in response_data
    print("✅ File CREATE working")

def test_file_read():
    file_content = b"Test file content for CRUD"
    files = {"file": ("test_crud.txt", io.BytesIO(file_content), "text/plain")}
    data = {"description": "CRUD test file", "user_id": "crud_test_user"}
    
    response = requests.post("http://localhost:8003/upload", files=files, data=data)
    file_id = response.json()["_id"]
    
    response = requests.get(f"http://localhost:8003/files/{file_id}")
    assert response.status_code == 200
    print("✅ File READ working")

def test_file_delete():
    file_content = b"Test file content for CRUD"
    files = {"file": ("test_crud.txt", io.BytesIO(file_content), "text/plain")}
    data = {"description": "CRUD test file", "user_id": "crud_test_user"}
    
    response = requests.post("http://localhost:8003/upload", files=files, data=data)
    file_id = response.json()["_id"]
    
    response = requests.delete(f"http://localhost:8003/files/{file_id}")
    assert response.status_code in [200, 204]
    print("✅ File DELETE working")
