#!/usr/bin/env python
import os
import django
import json
import yaml
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_schema_from_config

def export_openapi_schema():
    """Export OpenAPI schema to files"""
    # Generate schema
    schema = build_schema_from_config()
    
    # Ensure docs directory exists
    docs_dir = Path('docs/api')
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Export as JSON
    with open(docs_dir / 'openapi.json', 'w') as f:
        json.dump(schema, f, indent=2)
    
    # Export as YAML
    with open(docs_dir / 'openapi.yaml', 'w') as f:
        yaml.dump(schema, f, default_flow_style=False)
    
    print(f"✅ OpenAPI schema exported to {docs_dir}/")
    
    return schema

def generate_postman_collection(schema):
    """Generate Postman collection from OpenAPI schema"""
    from openapi_to_postman import convert
    
    # Convert OpenAPI to Postman
    postman_collection = convert(schema)
    
    # Save collection
    with open('docs/api/postman_collection.json', 'w') as f:
        json.dump(postman_collection, f, indent=2)
    
    print("✅ Postman collection generated")

if __name__ == "__main__":
    schema = export_openapi_schema()
    generate_postman_collection(schema)