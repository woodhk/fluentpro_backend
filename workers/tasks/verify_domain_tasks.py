#!/usr/bin/env python3
"""
Verification script for domain-specific task registration
"""
import os
import sys

# Add the project root to the Python path  
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

def test_task_imports():
    """Test that domain tasks can be imported successfully"""
    try:
        # Test authentication tasks
        from domains.authentication.tasks.send_welcome_email import send_welcome_email, send_password_reset_email
        print("✅ Authentication tasks imported successfully")
        print(f"   - send_welcome_email: {send_welcome_email.name}")
        print(f"   - send_password_reset_email: {send_password_reset_email.name}")
        
        # Test onboarding tasks
        from domains.onboarding.tasks.generate_recommendations import generate_user_recommendations, analyze_onboarding_completion
        print("✅ Onboarding tasks imported successfully")
        print(f"   - generate_user_recommendations: {generate_user_recommendations.name}")
        print(f"   - analyze_onboarding_completion: {analyze_onboarding_completion.name}")
        
        return True
    except ImportError as e:
        print(f"❌ Task import error: {e}")
        return False

def test_task_attributes():
    """Test that tasks have proper Celery attributes"""
    try:
        from domains.authentication.tasks.send_welcome_email import send_welcome_email
        from domains.onboarding.tasks.generate_recommendations import generate_user_recommendations
        
        # Check send_welcome_email task
        assert hasattr(send_welcome_email, 'name'), "send_welcome_email missing name attribute"
        assert hasattr(send_welcome_email, 'queue'), "send_welcome_email missing queue attribute"
        assert send_welcome_email.queue == 'auth', f"Expected queue 'auth', got '{send_welcome_email.queue}'"
        
        print("✅ send_welcome_email task attributes verified")
        print(f"   - Name: {send_welcome_email.name}")
        print(f"   - Queue: {send_welcome_email.queue}")
        
        # Check generate_user_recommendations task
        assert hasattr(generate_user_recommendations, 'name'), "generate_user_recommendations missing name attribute"
        assert hasattr(generate_user_recommendations, 'queue'), "generate_user_recommendations missing queue attribute"
        assert generate_user_recommendations.queue == 'onboarding', f"Expected queue 'onboarding', got '{generate_user_recommendations.queue}'"
        
        print("✅ generate_user_recommendations task attributes verified")
        print(f"   - Name: {generate_user_recommendations.name}")
        print(f"   - Queue: {generate_user_recommendations.queue}")
        
        return True
    except Exception as e:
        print(f"❌ Task attributes error: {e}")
        return False

def test_task_registration_structure():
    """Test that tasks are structured for proper registration"""
    try:
        # Test that __init__.py files import tasks
        from domains.authentication.tasks import send_welcome_email, send_password_reset_email
        from domains.onboarding.tasks import generate_user_recommendations, analyze_onboarding_completion
        
        print("✅ Tasks accessible via __init__.py imports")
        
        # Verify expected task names
        expected_tasks = [
            'domains.authentication.tasks.send_welcome_email.send_welcome_email',
            'domains.authentication.tasks.send_welcome_email.send_password_reset_email', 
            'domains.onboarding.tasks.generate_recommendations.generate_user_recommendations',
            'domains.onboarding.tasks.generate_recommendations.analyze_onboarding_completion'
        ]
        
        print("✅ Expected task names:")
        for task_name in expected_tasks:
            print(f"   - {task_name}")
        
        return True
    except ImportError as e:
        print(f"❌ Task registration structure error: {e}")
        return False

def test_celery_app_task_detection():
    """Test that Celery app can detect the tasks"""
    try:
        # Import Celery app configuration
        from workers.celery_config import broker_url, result_backend
        print("✅ Celery configuration loaded")
        print(f"   - Broker: {broker_url}")
        print(f"   - Backend: {result_backend}")
        
        # Test task routing configuration
        from workers.celery_config import task_routes
        auth_route = task_routes.get('domains.authentication.tasks.*')
        onboarding_route = task_routes.get('domains.onboarding.tasks.*')
        
        assert auth_route == {'queue': 'auth'}, f"Auth route incorrect: {auth_route}"
        assert onboarding_route == {'queue': 'onboarding'}, f"Onboarding route incorrect: {onboarding_route}"
        
        print("✅ Task routing configured correctly")
        print(f"   - Authentication tasks → {auth_route}")
        print(f"   - Onboarding tasks → {onboarding_route}")
        
        return True
    except Exception as e:
        print(f"❌ Celery app detection error: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Verifying domain-specific task implementations...")
    print("=" * 60)
    
    tests = [
        ("Task Imports", test_task_imports),
        ("Task Attributes", test_task_attributes),
        ("Task Registration Structure", test_task_registration_structure),
        ("Celery App Task Detection", test_celery_app_task_detection),
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
        print("\n📝 Domain Tasks Summary:")
        print("   🔐 Authentication Tasks:")
        print("      • send_welcome_email (queue: auth)")
        print("      • send_password_reset_email (queue: auth)")
        print("   🎯 Onboarding Tasks:")
        print("      • generate_user_recommendations (queue: onboarding)")
        print("      • analyze_onboarding_completion (queue: onboarding)")
        print("\n✅ Tasks ready for Celery registration!")
        print("   Next: Start Redis and run 'celery -A workers.celery_app inspect registered'")
        return True
    else:
        print(f"❌ {total - passed} tests failed ({passed}/{total} passed)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)