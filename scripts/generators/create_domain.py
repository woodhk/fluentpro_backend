#!/usr/bin/env python
import os
import sys
from pathlib import Path
from typing import Optional
import click

TEMPLATE_DIR = Path(__file__).parent / "templates"

@click.command()
@click.argument('domain_name')
@click.option('--with-api', is_flag=True, help='Include API layer')
def create_domain(domain_name: str, with_api: bool):
    """Create a new domain with standard structure"""
    domain_path = Path(f"domains/{domain_name}")
    
    if domain_path.exists():
        click.echo(f"\u274c Domain {domain_name} already exists")
        sys.exit(1)
    
    # Create directory structure
    directories = [
        "",
        "models",
        "repositories",
        "services",
        "use_cases",
        "dto",
        "events",
        "tasks",
    ]
    
    if with_api:
        directories.extend(["api", "api/v1"])
    
    for dir_name in directories:
        dir_path = domain_path / dir_name
        dir_path.mkdir(parents=True)
        
        # Create __init__.py
        (dir_path / "__init__.py").touch()
    
    # Create standard files from templates
    create_file_from_template(
        "domain_models.py.template",
        domain_path / "models" / "__init__.py",
        {"domain_name": domain_name}
    )
    
    create_file_from_template(
        "domain_interfaces.py.template",
        domain_path / "repositories" / "interfaces.py",
        {"domain_name": domain_name}
    )
    
    create_file_from_template(
        "domain_dto.py.template",
        domain_path / "dto" / "requests.py",
        {"domain_name": domain_name}
    )
    
    click.echo(f"\u2705 Created domain: {domain_name}")
    click.echo("\nNext steps:")
    click.echo("1. Define your domain models")
    click.echo("2. Create repository interfaces")
    click.echo("3. Implement use cases")
    click.echo("4. Add to application container")

def create_file_from_template(template_name: str, target_path: Path, context: dict):
    """Create file from template with variable substitution"""
    template_path = TEMPLATE_DIR / template_name
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Simple template substitution
    for key, value in context.items():
        content = content.replace(f"{{{{ {key} }}}}", value)
        content = content.replace(f"{{{{ {key}.title() }}}}", value.title())
    
    with open(target_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    create_domain()