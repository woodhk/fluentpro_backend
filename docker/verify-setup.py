#!/usr/bin/env python3
"""
Verification script for Docker Compose and Flower setup
"""
import os
import sys
import yaml

def test_docker_compose_files():
    """Test that Docker Compose files exist and are valid"""
    files_to_check = [
        'docker-compose.yml',
        'docker-compose.override.yml'
    ]
    
    for filename in files_to_check:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(filepath):
            print(f"❌ Missing file: {filename}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                config = yaml.safe_load(f)
            print(f"✅ {filename} - Valid YAML")
            
            # Check required services in main compose file
            if filename == 'docker-compose.yml':
                required_services = ['redis', 'celery_worker', 'flower']
                services = config.get('services', {})
                
                for service in required_services:
                    if service in services:
                        print(f"   ✅ Service '{service}' defined")
                    else:
                        print(f"   ❌ Missing service: {service}")
                        return False
                        
                # Check Flower port mapping
                flower_config = services.get('flower', {})
                ports = flower_config.get('ports', [])
                if '5555:5555' in ports:
                    print(f"   ✅ Flower port 5555 mapped correctly")
                else:
                    print(f"   ❌ Flower port 5555 not mapped correctly")
                    return False
                    
        except yaml.YAMLError as e:
            print(f"❌ {filename} - Invalid YAML: {e}")
            return False
    
    return True

def test_helper_scripts():
    """Test that helper scripts exist and are executable"""
    scripts = ['start-services.sh', 'stop-services.sh']
    
    for script in scripts:
        script_path = os.path.join(os.path.dirname(__file__), script)
        if not os.path.exists(script_path):
            print(f"❌ Missing script: {script}")
            return False
        
        if not os.access(script_path, os.X_OK):
            print(f"❌ Script not executable: {script}")
            return False
        
        print(f"✅ {script} exists and is executable")
    
    return True

def test_flower_config():
    """Test Flower configuration file"""
    config_path = os.path.join(os.path.dirname(__file__), 'flower_config.py')
    
    if not os.path.exists(config_path):
        print("❌ Missing flower_config.py")
        return False
    
    try:
        # Basic syntax check
        with open(config_path, 'r') as f:
            content = f.read()
            compile(content, config_path, 'exec')
        
        print("✅ flower_config.py - Valid Python syntax")
        
        # Check for required configurations
        required_configs = ['basic_auth', 'auto_refresh', 'enable_events']
        for config in required_configs:
            if config in content:
                print(f"   ✅ Configuration '{config}' present")
            else:
                print(f"   ❌ Missing configuration: {config}")
                return False
                
    except SyntaxError as e:
        print(f"❌ flower_config.py - Syntax error: {e}")
        return False
    
    return True

def test_dockerfile_updates():
    """Test that Dockerfile has been updated for requirements structure"""
    dockerfile_path = os.path.join(os.path.dirname(__file__), '..', 'Dockerfile')
    
    if not os.path.exists(dockerfile_path):
        print("❌ Missing Dockerfile")
        return False
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check for requirements structure support
    if 'requirements/' in content:
        print("✅ Dockerfile supports requirements/ structure")
    else:
        print("❌ Dockerfile not updated for requirements/ structure")
        return False
    
    # Check for curl installation (needed for health checks)
    if 'curl' in content:
        print("✅ Dockerfile includes curl for health checks")
    else:
        print("❌ Dockerfile missing curl for health checks")
        return False
    
    return True

def test_requirements_flower():
    """Test that Flower is in development requirements"""
    req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements', 'development.txt')
    
    if not os.path.exists(req_path):
        print("❌ Missing requirements/development.txt")
        return False
    
    with open(req_path, 'r') as f:
        content = f.read()
    
    if 'flower' in content.lower():
        print("✅ Flower included in development requirements")
        return True
    else:
        print("❌ Flower missing from development requirements")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Verifying Docker Compose and Flower setup...")
    print("=" * 60)
    
    tests = [
        ("Docker Compose Files", test_docker_compose_files),
        ("Helper Scripts", test_helper_scripts),
        ("Flower Configuration", test_flower_config),
        ("Dockerfile Updates", test_dockerfile_updates),
        ("Requirements (Flower)", test_requirements_flower),
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
        print("\n📝 Setup Complete:")
        print("   ✅ Docker Compose configuration ready")
        print("   ✅ Flower monitoring dashboard configured")
        print("   ✅ Helper scripts available")
        print("   ✅ Health checks configured")
        print("\n🚀 Next Steps:")
        print("   1. Run: cd docker && ./start-services.sh")
        print("   2. Open: http://localhost:5555 (admin/dev123)")
        print("   3. Monitor Celery tasks and workers")
        return True
    else:
        print(f"❌ {total - passed} tests failed ({passed}/{total} passed)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)