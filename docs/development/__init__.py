"""
FluentPro Development Documentation

This package contains comprehensive documentation for FluentPro backend development,
deployment, and operational procedures.

Modules:
    environment_setup: Local development environment setup guide
    deployment: Production and staging deployment procedures
    
See also:
    ../troubleshooting.md: Common issues and solutions
    ../README.md: Quick start guide
"""

__version__ = "1.0.0"
__author__ = "FluentPro Development Team"

# Documentation structure
DOCS_STRUCTURE = {
    "environment_setup": "Local development environment setup and configuration",
    "deployment": "Production and staging deployment procedures and best practices",
    "troubleshooting": "Common issues, debugging tips, and solutions",
}

def get_documentation_overview():
    """Return an overview of available documentation."""
    return DOCS_STRUCTURE