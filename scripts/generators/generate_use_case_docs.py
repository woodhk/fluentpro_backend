"""
Generate documentation for all use cases in the project.

This script scans the domains directory for use case classes and generates
markdown documentation based on their docstrings.
"""

import inspect
import importlib
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class UseCase:
    """Mock base class for type checking."""
    pass


def extract_docstring_sections(docstring: str) -> Dict[str, Any]:
    """Extract structured information from use case docstrings."""
    sections = {
        'description': '',
        'flow': [],
        'errors': [],
        'dependencies': []
    }
    
    if not docstring:
        return sections
    
    lines = docstring.strip().split('\n')
    current_section = 'description'
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # Check for section headers
        if line.startswith('Flow:'):
            if current_section == 'description':
                sections['description'] = '\n'.join(current_content).strip()
            current_section = 'flow'
            current_content = []
        elif line.startswith('Errors:'):
            if current_section == 'flow':
                sections['flow'] = [item.strip() for item in current_content if item.strip()]
            current_section = 'errors'
            current_content = []
        elif line.startswith('Dependencies:'):
            if current_section == 'errors':
                sections['errors'] = [item.strip() for item in current_content if item.strip()]
            current_section = 'dependencies'
            current_content = []
        elif line:
            # Remove list markers and add to current content
            if line.startswith(('- ', '* ', '1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')):
                # Extract the content after the list marker
                content = re.sub(r'^[-*\d.]\s+', '', line)
                current_content.append(content)
            elif current_section == 'description' or not line.startswith(' '):
                current_content.append(line)
    
    # Handle the last section
    if current_section == 'description':
        sections['description'] = '\n'.join(current_content).strip()
    elif current_section == 'flow':
        sections['flow'] = [item.strip() for item in current_content if item.strip()]
    elif current_section == 'errors':
        sections['errors'] = [item.strip() for item in current_content if item.strip()]
    elif current_section == 'dependencies':
        sections['dependencies'] = [item.strip() for item in current_content if item.strip()]
    
    return sections


def get_use_case_info(module_path: Path, class_name: str) -> Optional[Dict[str, Any]]:
    """Extract use case information from a Python file by parsing the source code."""
    try:
        # Read the file content
        content = module_path.read_text()
        
        # Find the class definition and its docstring
        class_pattern = rf'class\s+{class_name}[^:]*:\s*"""(.*?)"""'
        match = re.search(class_pattern, content, re.DOTALL)
        
        if not match:
            # Try single line docstring
            class_pattern = rf'class\s+{class_name}[^:]*:\s*"([^"]*)"'
            match = re.search(class_pattern, content, re.DOTALL)
        
        if match:
            docstring = match.group(1).strip()
            sections = extract_docstring_sections(docstring)
            
            # Try to extract execute method signature
            execute_pattern = r'def\s+execute\s*\([^)]*\)[^:]*:'
            execute_match = re.search(execute_pattern, content)
            method_signature = "(self, ...)" if execute_match else ""
            
            # Get domain from path
            relative_path = module_path.relative_to(project_root)
            
            return {
                'name': class_name,
                'module': str(relative_path).replace('/', '.').replace('.py', ''),
                'domain': relative_path.parts[1] if len(relative_path.parts) > 1 else 'unknown',
                'file': str(relative_path),
                'docstring': docstring,
                'sections': sections,
                'signature': method_signature
            }
        
        return None
        
    except Exception as e:
        print(f"Error processing {module_path}: {e}")
        return None


def find_all_use_cases() -> List[Dict[str, Any]]:
    """Find all use case classes in the domains directory."""
    use_cases = []
    domains_path = project_root / 'domains'
    
    # Find all Python files in use_cases directories
    for domain_path in domains_path.iterdir():
        if domain_path.is_dir() and not domain_path.name.startswith('__'):
            use_case_path = domain_path / 'use_cases'
            if use_case_path.exists():
                for file_path in use_case_path.glob('*.py'):
                    if file_path.name not in ['__init__.py', 'factory.py']:
                        # Read file to find class names
                        content = file_path.read_text()
                        # Find all class definitions that contain "UseCase" or are use cases without "UseCase" in name
                        class_pattern = r'class\s+(\w+)\s*[\(:]'
                        matches = re.findall(class_pattern, content)
                        # Filter to only include use case classes
                        matches = [m for m in matches if 'UseCase' in m or m in ['SelectUserIndustry', 'SelectNativeLanguage', 'MatchUserRoleFromDescription']]
                        
                        for class_name in matches:
                            info = get_use_case_info(file_path, class_name)
                            if info:
                                use_cases.append(info)
    
    # Sort by domain and name
    use_cases.sort(key=lambda x: (x['domain'], x['name']))
    return use_cases


def generate_markdown_documentation(use_cases: List[Dict[str, Any]]) -> str:
    """Generate markdown documentation from use case information."""
    lines = ["# Use Cases Documentation", ""]
    lines.append("This document provides comprehensive documentation for all use cases in the FluentPro backend.")
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")
    
    # Group by domain
    domains = {}
    for uc in use_cases:
        domain = uc['domain']
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(uc)
    
    # Generate TOC
    for domain in sorted(domains.keys()):
        lines.append(f"- [{domain.title()} Domain](#{domain}-domain)")
        for uc in domains[domain]:
            anchor = uc['name'].lower().replace('_', '-')
            lines.append(f"  - [{uc['name']}](#{anchor})")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Generate detailed documentation
    for domain in sorted(domains.keys()):
        lines.append(f"## {domain.title()} Domain")
        lines.append("")
        
        for uc in domains[domain]:
            lines.append(f"### {uc['name']}")
            lines.append("")
            
            # File location
            lines.append(f"**File:** `{uc['file']}`")
            lines.append("")
            
            # Description
            if uc['sections']['description']:
                lines.append("**Description:**")
                lines.append(uc['sections']['description'])
                lines.append("")
            
            # Signature
            if uc['signature']:
                lines.append("**Signature:**")
                lines.append(f"```python")
                lines.append(f"execute{uc['signature']}")
                lines.append("```")
                lines.append("")
            
            # Flow
            if uc['sections']['flow']:
                lines.append("**Flow:**")
                for i, step in enumerate(uc['sections']['flow'], 1):
                    lines.append(f"{i}. {step}")
                lines.append("")
            
            # Errors
            if uc['sections']['errors']:
                lines.append("**Errors:**")
                for error in uc['sections']['errors']:
                    lines.append(f"- {error}")
                lines.append("")
            
            # Dependencies
            if uc['sections']['dependencies']:
                lines.append("**Dependencies:**")
                for dep in uc['sections']['dependencies']:
                    lines.append(f"- {dep}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    return '\n'.join(lines)


def main():
    """Main function to generate use case documentation."""
    print("Scanning for use cases...")
    use_cases = find_all_use_cases()
    
    print(f"Found {len(use_cases)} use cases")
    
    # Generate markdown
    markdown = generate_markdown_documentation(use_cases)
    
    # Create docs directory if it doesn't exist
    docs_dir = project_root / 'docs'
    docs_dir.mkdir(exist_ok=True)
    
    # Write documentation
    output_file = docs_dir / 'use_cases.md'
    output_file.write_text(markdown)
    
    print(f"Documentation generated: {output_file}")
    
    # Print summary
    domains = {}
    for uc in use_cases:
        domain = uc['domain']
        if domain not in domains:
            domains[domain] = 0
        domains[domain] += 1
    
    print("\nSummary by domain:")
    for domain, count in sorted(domains.items()):
        print(f"  {domain}: {count} use cases")


if __name__ == "__main__":
    main()