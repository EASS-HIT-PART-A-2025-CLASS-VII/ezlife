# Setup local development environment
$ErrorActionPreference = "Stop"

Write-Host "Setting up EZLife local development environment..." -ForegroundColor Cyan

# Check if MongoDB is installed or running
$mongoRunning = $false
try {
    $mongodProcess = Get-Process mongod -ErrorAction SilentlyContinue
    if ($mongodProcess) {
        Write-Host "✅ MongoDB is already running!" -ForegroundColor Green
        $mongoRunning = $true
    }
} catch {
    Write-Host "MongoDB is not running. Will try to start it." -ForegroundColor Yellow
}

# If MongoDB isn't running, try to start it
if (-not $mongoRunning) {
    try {
        # Try to start MongoDB as a service
        Start-Service mongodb -ErrorAction SilentlyContinue
        Write-Host "✅ Started MongoDB service!" -ForegroundColor Green
        $mongoRunning = $true
    } catch {
        Write-Host "Could not start MongoDB as a service." -ForegroundColor Yellow
        
        # Check if MongoDB is installed via command line
        try {
            mongod --version | Out-Null
            Write-Host "MongoDB is installed. Starting MongoDB in the background..." -ForegroundColor Yellow
            Start-Process mongod -ArgumentList "--dbpath=C:\data\db" -WindowStyle Hidden
            Write-Host "✅ Started MongoDB manually!" -ForegroundColor Green
            $mongoRunning = $true
        } catch {
            Write-Host "❌ MongoDB is not installed or not in PATH. Please install MongoDB or use Docker." -ForegroundColor Red
            Write-Host "Download MongoDB: https://www.mongodb.com/try/download/community" -ForegroundColor Blue
            Write-Host "Or use Docker: docker run -d -p 27017:27017 --name mongodb mongo" -ForegroundColor Blue
            Exit 1
        }
    }
}

# Configure local development
Write-Host "Setting up backend configuration..." -ForegroundColor Cyan
cd c:\Users\Leon\Desktop\EZlife\backend

# Update .env file for local development
$envContent = @"
# MongoDB Local URI for development
MONGO_URI=mongodb://localhost:27017/task_management

# OpenRouter API Key
OPENROUTER_API_KEY=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

# Comment out the Atlas URI to use local MongoDB
# MONGO_URI=mongodb+srv://ezlifedb:<db_password>@ezlife.tyhljcz.mongodb.net/?retryWrites=true&w=majority&appName=EZLife
"@

Set-Content -Path ".env" -Value $envContent

# Setup local MongoDB with sample data
Write-Host "Setting up local MongoDB with sample data..." -ForegroundColor Cyan
python setup_local_mongodb.py

# Start the backend
Write-Host "Starting backend server..." -ForegroundColor Cyan
Start-Process python -ArgumentList "main.py" -NoNewWindow

# Wait a moment for the backend to start
Start-Sleep -Seconds 3

# Start frontend in development mode
Write-Host "Starting frontend..." -ForegroundColor Cyan
cd c:\Users\Leon\Desktop\EZlife\frontend
npm install
npm run dev

Write-Host "EZLife application is running!" -ForegroundColor Green
