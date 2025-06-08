#!/usr/bin/env python
import ast
import os
from pathlib import Path
from typing import Set, Dict, List

class ImportAuditor(ast.NodeVisitor):
    def __init__(self, current_domain: str):
        self.current_domain = current_domain
        self.imports: Set[str] = set()
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)

def audit_domain_imports(domain_name: str) -> Dict[str, List[str]]:
    """Find all cross-domain imports in a domain"""
    violations = {}
    domain_path = Path(f"domains/{domain_name}")
    
    for py_file in domain_path.rglob("*.py"):
        with open(py_file, 'r') as f:
            tree = ast.parse(f.read())
        
        auditor = ImportAuditor(domain_name)
        auditor.visit(tree)
        
        # Check for cross-domain imports
        file_violations = []
        for import_name in auditor.imports:
            if import_name.startswith("domains.") and domain_name not in import_name:
                if not import_name.startswith("domains.shared"):
                    file_violations.append(import_name)
        
        if file_violations:
            violations[str(py_file)] = file_violations
    
    return violations

def main():
    print("Auditing cross-domain imports...\n")
    
    domains = [d.name for d in Path("domains").iterdir() if d.is_dir() and d.name != "shared"]
    
    all_violations = {}
    for domain in domains:
        violations = audit_domain_imports(domain)
        if violations:
            all_violations[domain] = violations
    
    if all_violations:
        print("❌ Cross-domain import violations found:\n")
        for domain, files in all_violations.items():
            print(f"Domain: {domain}")
            for file, imports in files.items():
                print(f"  {file}:")
                for imp in imports:
                    print(f"    - {imp}")
        return False
    else:
        print("✅ No cross-domain imports found")
        return True

if __name__ == "__main__":
    import sys
    if not main():
        sys.exit(1)