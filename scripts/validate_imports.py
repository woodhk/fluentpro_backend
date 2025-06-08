#!/usr/bin/env python
import subprocess
import sys

def validate_imports():
    """Run import-linter to validate architecture"""
    result = subprocess.run(
        ["lint-imports"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("\u274c Import violations detected:")
        print(result.stdout)
        print(result.stderr)
        return False
    
    print("\u2705 All import rules passed")
    return True

if __name__ == "__main__":
    if not validate_imports():
        sys.exit(1)