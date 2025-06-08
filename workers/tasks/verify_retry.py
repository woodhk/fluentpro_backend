#!/usr/bin/env python3
"""
Verification script for testing retry behavior
This script can be run independently to verify the task structure is correct
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

def test_task_imports():
    """Test that all task classes can be imported successfully"""
    try:
        from workers.tasks.base_task import BaseTask, CriticalTask, QuickTask
        from workers.tasks.test_task import test_retry_task, test_deterministic_failure_task, test_always_fail_task
        print("✅ All task classes imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_celery_app():
    """Test that Celery app can be imported and configured"""
    try:
        from workers.celery_app import app
        print("✅ Celery app imported successfully")
        print(f"   App name: {app.main}")
        print(f"   Broker URL: {app.conf.broker_url}")
        return True
    except ImportError as e:
        print(f"❌ Celery app import error: {e}")
        return False

def test_retry_decorator():
    """Test that retry decorators can be imported"""
    try:
        from application.decorators.retry import retry, celery_retry_on_failure
        print("✅ Retry decorators imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Retry decorator import error: {e}")
        return False

def test_task_registration():
    """Test that tasks are properly registered with Celery"""
    try:
        from workers.celery_app import app
        registered_tasks = list(app.tasks.keys())
        expected_tasks = [
            'workers.tasks.test_task.test_retry_task',
            'workers.tasks.test_task.test_deterministic_failure_task', 
            'workers.tasks.test_task.test_always_fail_task'
        ]
        
        print(f"✅ Found {len(registered_tasks)} registered tasks")
        for task in expected_tasks:
            if task in registered_tasks:
                print(f"   ✅ {task}")
            else:
                print(f"   ❌ {task} (missing)")
        
        return all(task in registered_tasks for task in expected_tasks)
    except Exception as e:
        print(f"❌ Task registration test error: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Verifying Celery task setup and retry behavior...")
    print("=" * 60)
    
    tests = [
        ("Task Imports", test_task_imports),
        ("Celery App", test_celery_app),
        ("Retry Decorators", test_retry_decorator),
        ("Task Registration", test_task_registration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}:")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n📝 Next steps:")
        print("   1. Start Redis server: redis-server")
        print("   2. Start Celery worker: celery -A workers.celery_app worker --loglevel=info")
        print("   3. Test retry behavior by calling tasks")
        return True
    else:
        print(f"❌ {total - passed} tests failed ({passed}/{total} passed)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)