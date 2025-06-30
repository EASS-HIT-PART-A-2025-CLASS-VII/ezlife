import sys
import subprocess
import requests

SERVICES = {
    'USER': 'http://localhost:8001/health',
    'FILE': 'http://localhost:8003/health', 
    'TASK': 'http://localhost:8002/health',
    'MAIN': 'http://localhost:8000/health'
}

TEST_FILES = {
    'USER': 'test_user_service.py',
    'FILE': 'test_file_service.py',
    'TASK': 'test_task_estimation_service.py',
    'USER_HEALTH': 'test_user_health.py',
    'FILE_HEALTH': 'test_file_health.py',
    'TASK_HEALTH': 'test_task_estimation_health.py'
}

def check_services():
    print("Checking services...")
    for service_name, url in SERVICES.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} service is healthy")
            else:
                print(f"❌ {service_name} service unhealthy")
                return False
        except:
            print(f"❌ {service_name} service not responding")
            return False
    return True

def run_tests(test_type=None):
    if not check_services():
        return False
    
    cmd = [sys.executable, '-m', 'pytest']
    
    if test_type:
        if test_type in TEST_FILES:
            cmd.append(TEST_FILES[test_type])
        else:
            print(f"Unknown test type: {test_type}")
            return False
    else:
        for test_file in TEST_FILES.values():
            cmd.append(test_file)
    
    cmd.extend(['-v', '--tb=short'])
    
    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except:
        return False

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', choices=list(TEST_FILES.keys()), help='Run specific test')
    args = parser.parse_args()
    
    success = run_tests(args.test)
    sys.exit(0 if success else 1)
