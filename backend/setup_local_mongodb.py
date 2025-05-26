# Local MongoDB configuration for development/testing
import os
from pymongo import MongoClient
import datetime
import json
import sys

def setup_local_mongodb():
    """Set up and populate a local MongoDB for testing"""
    print("Setting up local MongoDB for development...")
    
    # Connect to local MongoDB
    try:
        client = MongoClient('mongodb://localhost:27017/')
        print("✅ Connected to local MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to local MongoDB: {str(e)}")
        print("Please ensure MongoDB is installed and running locally.")
        print("You can download it from: https://www.mongodb.com/try/download/community")
        print("Or use Docker: docker run -d -p 27017:27017 --name mongodb mongo")
        sys.exit(1)
    
    # Create/use the task_management database
    db = client.task_management
    
    # Drop existing collections to start fresh
    if 'drop_existing' in sys.argv:
        print("⚠️ Dropping existing collections...")
        db.tasks.drop()
        db.users.drop()
    
    # Create test user
    users_collection = db.users
    
    if users_collection.count_documents({'email': 'test@test.com'}) == 0:
        users_collection.insert_one({
            'email': 'test@test.com',
            'password': '$2b$12$CwsW3AQC0xgH/rVKvddVyejS0tHT3z2j2TeFTRXVtT7jxSGcQybYO',  # bcrypt hash for '12345678'
            'created_at': datetime.datetime.utcnow()
        })
        print("✅ Created test user: test@test.com (password: 12345678)")
    else:
        print("ℹ️ Test user already exists")
    
    # Create sample tasks with breakdown
    tasks_collection = db.tasks
    
    if tasks_collection.count_documents({}) == 0:
        # Create a task without breakdown
        tasks_collection.insert_one({
            'description': 'Welcome to EZlife! This is a sample task.',
            'completed': False,
            'estimated_minutes': 30,
            'created_at': datetime.datetime.utcnow(),
            'due_date': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        })
        
        # Create a task with breakdown
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        sample_breakdown = [
            {
                'day': 'Day 1',
                'date': (today + datetime.timedelta(days=0)).strftime('%Y-%m-%d'),
                'hours': 2.0,
                'summary': 'Research and planning phase. Gather requirements and define project scope.',
                'completed': True
            },
            {
                'day': 'Day 2',
                'date': (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                'hours': 3.0,
                'summary': 'Start implementation. Set up project structure and implement core functionality.',
                'completed': False
            },
            {
                'day': 'Day 3',
                'date': (today + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
                'hours': 2.5,
                'summary': 'Continue development. Implement remaining features and start testing.',
                'completed': False
            }
        ]
        
        tasks_collection.insert_one({
            'description': 'Build a simple web application with task breakdown',
            'completed': False,
            'estimated_minutes': 450,  # 7.5 hours total
            'created_at': datetime.datetime.utcnow(),
            'due_date': today + datetime.timedelta(days=3),
            'days_per_week': 5,
            'hours_per_day': 3.0,
            'breakdown': sample_breakdown,
            'progress': 33.33  # 1/3 days completed
        })
        
        print(f"✅ Created {tasks_collection.count_documents({})} sample tasks")
    else:
        print(f"ℹ️ {tasks_collection.count_documents({})} tasks already exist")
    
    # Update the .env file to use local MongoDB
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    if 'mongodb://localhost:27017' not in env_content:
        env_content = env_content.replace(
            'MONGO_URI=mongodb+srv://', 
            '# MongoDB Atlas URI (commented out due to authentication issues)\n# MONGO_URI=mongodb+srv://'
        )
        
        if 'mongodb://localhost:27017' not in env_content:
            env_content += '\n\n# Local MongoDB for development\nMONGO_URI=mongodb://localhost:27017\n'
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("✅ Updated .env to use local MongoDB")
    
    print("\n✅ Local MongoDB setup complete!")
    print("✅ You can now run your application using the local database")
    print("✅ Connect with user: test@test.com and password: 12345678")

if __name__ == "__main__":
    setup_local_mongodb()
