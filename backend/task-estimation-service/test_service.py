import httpx
import asyncio
import time
from typing import Dict, Any

# URL of the task estimation service
SERVICE_URL = "http://localhost:8002/estimate_time"

# Test tasks to send to the service
TEST_TASKS = [
    {
        "description": "Write a 5-page report on renewable energy",
        "days_per_week": 5,
        "hours_per_day": 2.0
    },
    {
        "description": "Organize a team meeting with 10 people",
        "days_per_week": 5, 
        "hours_per_day": 1.0
    },
    {
        "description": "Develop a simple calculator app",
        "days_per_week": 3,
        "hours_per_day": 3.0
    },
    {
        "description": "Learn basic Spanish",
        "days_per_week": 7,
        "hours_per_day": 0.5
    }
]

async def test_estimation_service(task_data: Dict[str, Any]) -> None:
    """Test the task estimation service with a single task"""
    print(f"\n🔍 Testing task: {task_data['description']}")
    
    try:
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.post(SERVICE_URL, json=task_data, timeout=30.0)
            
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response time: {response_time:.2f}s")
            print(f"⏱ Estimated minutes: {result['estimated_minutes']}")
            print(f"🔄 Source: {result['source']}")
            
            if result.get('breakdown'):
                print(f"📋 Breakdown: {len(result['breakdown'])} days")
                for day in result['breakdown'][:2]:  # Show first 2 days only
                    print(f"  • {day['day']}: {day['hours']} hours - {day['summary'][:50]}...")
                if len(result['breakdown']) > 2:
                    print(f"  • ...and {len(result['breakdown'])-2} more days")
            else:
                print("❌ No breakdown received")
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except httpx.RequestError as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

async def run_tests() -> None:
    """Run tests for all test tasks"""
    print("🚀 Starting task estimation service tests")
    
    # Also test the health endpoint
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get("http://localhost:8002/health")
        
        if health_response.status_code == 200:
            print("✅ Health check successful")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test each task
    for task in TEST_TASKS:
        await test_estimation_service(task)
    
    print("\n✨ All tests completed")

if __name__ == "__main__":
    asyncio.run(run_tests())