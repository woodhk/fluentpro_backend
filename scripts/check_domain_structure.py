#!/usr/bin/env python
import os
import sys
from pathlib import Path

REQUIRED_SUBDIRS = [
    "models",
    "repositories",
    "services",
    "use_cases",
    "dto",
    "events",
    "tasks",
]


def check_domain_structure():
    """Validate that all domains have required structure"""
    domains_path = Path("domains")
    errors = []

    for domain_dir in domains_path.iterdir():
        if domain_dir.is_dir() and domain_dir.name not in ["shared", "__pycache__"]:
            for required_dir in REQUIRED_SUBDIRS:
                dir_path = domain_dir / required_dir
                if not dir_path.exists():
                    errors.append(f"Missing {required_dir} in {domain_dir.name}")
                elif not (dir_path / "__init__.py").exists():
                    errors.append(
                        f"Missing __init__.py in {domain_dir.name}/{required_dir}"
                    )

    if errors:
        print("\u274c Domain structure violations:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("\u2705 All domains have correct structure")
    return True


if __name__ == "__main__":
    if not check_domain_structure():
        sys.exit(1)
