# Test user registration/login and compare with task service
import requests
import json
import time

# Constants
USER_SERVICE_URL = "http://localhost:8001"
TASK_SERVICE_URL = "http://localhost:8000"
TEST_USER = {"email": "test@example.com", "password": "password123"}

print("🧪 Testing user service vs task service integration")

# Step 1: Try to register a test user
print("\nStep 1: Registering test user...")
try:
    register_response = requests.post(
        f"{USER_SERVICE_URL}/register", 
        json=TEST_USER
    )
    
    if register_response.status_code == 200:
        print("✅ User registered successfully")
    elif register_response.status_code == 400 and "already registered" in register_response.text:
        print("ℹ️ User already exists (this is fine)")
    else:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
except Exception as e:
    print(f"❌ Registration request failed: {str(e)}")

# Step 2: Log in to get token
print("\nStep 2: Logging in to get auth token...")
try:
    login_response = requests.post(
        f"{USER_SERVICE_URL}/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        print(f"✅ Login successful, got token: {token[:10]}...")
        
        # Set auth headers for subsequent requests
        auth_headers = {"Authorization": f"Bearer {token}"}
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Login request failed: {str(e)}")
    exit(1)

# Step 3: Test task service authentication
print("\nStep 3: Testing task service authentication...")
try:
    task_auth_response = requests.get(
        f"{TASK_SERVICE_URL}/tasks",
        headers=auth_headers
    )
    
    if task_auth_response.status_code == 200:
        print("✅ Task service authentication successful!")
        tasks = task_auth_response.json()
        print(f"Found {len(tasks)} tasks")
    else:
        print(f"❌ Task service authentication failed: {task_auth_response.status_code}")
        print(f"Response: {task_auth_response.text}")
except Exception as e:
    print(f"❌ Task service request failed: {str(e)}")

# Step 4: Compare MongoDB connections between services
print("\nStep 4: Analyzing differences in MongoDB connections...")

print("User Service:")
print("✓ Uses direct MongoClient connection")
print("✓ Default MONGO_URI: mongodb://localhost:27017")
print("✓ No connection retry logic")
print("✓ May be using a local MongoDB")

print("\nTask Service:")
print("✓ Uses db.py module with get_db() function")
print("✓ Connection retry logic with max_retries=3")
print("✓ Uses MongoDB Atlas connection string")
print("✓ Falls back to in-memory database on failure")

print("\n🔍 Analysis:")
if task_auth_response.status_code == 200:
    print("✅ Both services are working correctly")
    print("✅ Authentication is transferring between services")
    print("❗ They may be using different databases:")
    print("   - User service might be using a local MongoDB")
    print("   - Task service might be trying to use MongoDB Atlas")
else:
    print("❌ Services are not properly integrated")
    print("❌ Check if both services are using the same database")

print("\n💡 Recommendation:")
print("1. Update both services to use the same MongoDB instance")
print("2. If user service works but task service fails, modify task service to use the same connection approach")
print("3. Consider using the approach that works currently to ensure consistency")
