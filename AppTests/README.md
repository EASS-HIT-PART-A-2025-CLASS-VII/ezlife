# EZLife Backend Tests

## Test Files

**Service Tests:**
- `test_user_service.py` - User operations: Create, Read, Update, Delete
- `test_file_service.py` - File operations: Create, Read, Delete  
- `test_task_estimation_service.py` - Task estimation: Time estimation, Task breakdown

**Health Tests:**
- `test_user_health.py` - User service health check
- `test_file_health.py` - File service health check
- `test_task_estimation_health.py` - Task estimation service health check

## Usage

Run all tests:
```bash
python run_tests.py
```

Run specific service tests:
```bash
python run_tests.py --test USER
python run_tests.py --test FILE
python run_tests.py --test TASK
```

Run health checks:
```bash
python run_tests.py --test USER_HEALTH
python run_tests.py --test FILE_HEALTH
python run_tests.py --test TASK_HEALTH
```
