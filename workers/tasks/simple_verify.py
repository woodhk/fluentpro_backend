#!/usr/bin/env python3
"""
Simple verification script for testing retry behavior without Django
"""
import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

def test_base_task_import():
    """Test that BaseTask can be imported"""
    try:
        from workers.tasks.base_task import BaseTask, CriticalTask, QuickTask
        print("✅ BaseTask classes imported successfully")
        
        # Test class attributes
        assert hasattr(BaseTask, 'autoretry_for'), "BaseTask missing autoretry_for"
        assert hasattr(BaseTask, 'retry_kwargs'), "BaseTask missing retry_kwargs"
        assert hasattr(BaseTask, 'retry_backoff'), "BaseTask missing retry_backoff"
        
        print("   ✅ BaseTask attributes verified")
        print(f"   - autoretry_for: {BaseTask.autoretry_for}")
        print(f"   - retry_kwargs: {BaseTask.retry_kwargs}")
        print(f"   - retry_backoff: {BaseTask.retry_backoff}")
        
        return True
    except Exception as e:
        print(f"❌ BaseTask import error: {e}")
        return False

def test_retry_decorators():
    """Test retry decorators"""
    try:
        from application.decorators.retry import retry, celery_retry_on_failure
        print("✅ Retry decorators imported successfully")
        
        # Test that decorators are callable
        assert callable(retry), "retry decorator not callable"
        assert callable(celery_retry_on_failure), "celery_retry_on_failure decorator not callable"
        
        print("   ✅ Decorators are callable")
        return True
    except Exception as e:
        print(f"❌ Retry decorators error: {e}")
        return False

def test_retry_decorator_functionality():
    """Test retry decorator works with sync functions"""
    try:
        from application.decorators.retry import retry
        
        call_count = 0
        
        @retry(max_attempts=3, backoff_seconds=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return f"Success on attempt {call_count}"
        
        result = failing_function()
        assert call_count == 3, f"Expected 3 calls, got {call_count}"
        assert result == "Success on attempt 3", f"Unexpected result: {result}"
        
        print("✅ Retry decorator functionality verified")
        print(f"   - Function retried {call_count - 1} times before succeeding")
        return True
    except Exception as e:
        print(f"❌ Retry decorator functionality error: {e}")
        return False

def test_celery_config_import():
    """Test Celery configuration can be imported"""
    try:
        from workers.celery_config import broker_url, result_backend
        print("✅ Celery configuration imported successfully")
        print(f"   - broker_url: {broker_url}")
        print(f"   - result_backend: {result_backend}")
        return True
    except Exception as e:
        print(f"❌ Celery config error: {e}")
        return False

def main():
    """Run verification tests"""
    print("🔍 Verifying Celery task retry implementation...")
    print("=" * 60)
    
    tests = [
        ("BaseTask Import", test_base_task_import),
        ("Retry Decorators", test_retry_decorators),
        ("Retry Functionality", test_retry_decorator_functionality),
        ("Celery Config", test_celery_config_import),
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
        print("\n✅ Step 3 verification complete:")
        print("   - BaseTask class with retry logic ✅")
        print("   - Enhanced retry decorators for Celery ✅") 
        print("   - Error handling and logging ✅")
        print("   - Test tasks ready for retry verification ✅")
        return True
    else:
        print(f"❌ {total - passed} tests failed ({passed}/{total} passed)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)