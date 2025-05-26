# Setup development environment with Docker MongoDB
$ErrorActionPreference = "Stop"

Write-Host "Setting up EZLife local development environment with Docker MongoDB..." -ForegroundColor Cyan

# Check if Docker is installed
try {
    docker --version
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not in path" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if MongoDB container exists
$mongoExists = $false
try {
    $container = docker ps -a --filter "name=mongodb-ezlife" --format "{{.Names}}"
    if ($container -eq "mongodb-ezlife") {
        $mongoExists = $true
        Write-Host "✅ MongoDB container exists" -ForegroundColor Green
    }
} catch {
    # Container doesn't exist
}

# Start or create MongoDB container
if ($mongoExists) {
    # Check if it's running
    $running = docker ps --filter "name=mongodb-ezlife" --format "{{.Names}}"
    if ($running -eq "mongodb-ezlife") {
        Write-Host "✅ MongoDB container is already running" -ForegroundColor Green
    } else {
        Write-Host "Starting existing MongoDB container..." -ForegroundColor Yellow
        docker start mongodb-ezlife
        Write-Host "✅ MongoDB container started" -ForegroundColor Green
    }
} else {
    Write-Host "Creating MongoDB container..." -ForegroundColor Yellow
    docker run -d --name mongodb-ezlife -p 27017:27017 mongo:latest
    Write-Host "✅ MongoDB container created and started" -ForegroundColor Green
}

# Configure local development
Write-Host "Setting up backend configuration..." -ForegroundColor Cyan
cd C:\Users\Leon\Desktop\EZlife\backend

# Update .env file for local development
$envFileContent = @"
# Local MongoDB URI for development
MONGO_URI=mongodb://localhost:27017/task_management

# OpenRouter API Key - IMPORTANT: Replace with your actual key!
# You will need to create a .env file in the root of the project (EZlife/.env)
# and add your OPENROUTER_API_KEY there for docker-compose to pick it up.
# For local backend development (running main.py directly), 
# this script will create/update backend/.env
# For the task-estimation-service, ensure OPENROUTER_API_KEY is in EZlife/.env
OPENROUTER_API_KEY=your_openrouter_api_key_here_for_local_backend_dev_only 

# MongoDB Atlas URI (commented out due to connection issues)
# MONGO_URI=mongodb+srv://ezlifedb:ezlifedb@ezlife.tyhljcz.mongodb.net/?retryWrites=true&w=majority&appName=EZLife
"@

Set-Content -Path ".env" -Value $envFileContent
Write-Host "✅ Updated backend/.env. Please ensure OPENROUTER_API_KEY is also set in a root .env file for Docker." -ForegroundColor Green

# Create a .env.example in the root if it doesn't exist
$rootEnvExamplePath = "C:\\Users\\Leon\\Desktop\\EZlife\\.env.example"
if (-not (Test-Path $rootEnvExamplePath)) {
    $rootEnvExampleContent = @"
# This is an example .env file for Docker Compose.
# Copy this to .env in the same directory and fill in your actual values.

# For Main Backend and User Service (if they need separate env vars in future)
# MONGO_URI_BACKEND=mongodb+srv://...
# MONGO_URI_USER_SERVICE=mongodb+srv://...

# For Task Estimation Service
OPENROUTER_API_KEY=your_actual_openrouter_api_key_here
"@
    Set-Content -Path $rootEnvExamplePath -Value $rootEnvExampleContent
    Write-Host "✅ Created .env.example in the project root. Please copy to .env and update." -ForegroundColor Green
}

# Create a simplified setup script for the local MongoDB
$setupScript = @"
# Setup local MongoDB with sample data
from pymongo import MongoClient
import datetime
from passlib.context import CryptContext

print("Setting up local MongoDB with sample data...")

# Connect to local MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.task_management

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password):
    return pwd_context.hash(password)

# Create test user
if db.users.count_documents({'email': 'test@test.com'}) == 0:
    db.users.insert_one({
        'email': 'test@test.com',
        'password': hash_password('12345678'),
        'created_at': datetime.datetime.utcnow()
    })
    print("✅ Created test user: test@test.com (password: 12345678)")
else:
    print("ℹ️ Test user already exists")

# Create sample tasks with breakdown
if db.tasks.count_documents({}) == 0:
    # Create a task without breakdown
    db.tasks.insert_one({
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
    
    db.tasks.insert_one({
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
    
    print(f"✅ Created {db.tasks.count_documents({})} sample tasks")
else:
    print(f"ℹ️ {db.tasks.count_documents({})} tasks already exist")

print("✅ MongoDB setup completed successfully!")
"@

Set-Content -Path "setup_sample_data.py" -Value $setupScript

# Install required Python packages
Write-Host "Installing required Python packages..." -ForegroundColor Cyan
pip install pymongo passlib bcrypt

# Run the setup script
Write-Host "Setting up sample data..." -ForegroundColor Cyan
python setup_sample_data.py

# Start the backend server
Write-Host "`nStarting backend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\Leon\Desktop\EZlife\backend; python main.py"

# Start frontend development server
Write-Host "`nStarting frontend development server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\Leon\Desktop\EZlife\frontend; npm install; npm run dev"

Write-Host "`n✅ EZLife application is now running with local MongoDB" -ForegroundColor Green
Write-Host "Backend server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend server: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Login with: test@test.com / 12345678" -ForegroundColor Cyan
