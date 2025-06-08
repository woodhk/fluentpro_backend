from datetime import datetime, date
from typing import Optional
import warnings

class DeprecationWarning:
    def __init__(
        self,
        version: str,
        sunset_date: date,
        migration_guide: str,
        message: str = None
    ):
        self.version = version
        self.sunset_date = sunset_date
        self.migration_guide = migration_guide
        self.message = message or f"Version {version} is deprecated"
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "sunset_date": self.sunset_date.isoformat(),
            "migration_guide": self.migration_guide,
            "message": self.message
        }

def add_deprecation_warning(response_data: dict, warning: DeprecationWarning):
    """Add deprecation warning to response"""
    if "meta" not in response_data:
        response_data["meta"] = {}
    
    response_data["meta"]["deprecation"] = warning.to_dict()
    
    # Also log the warning
    warnings.warn(
        f"API {warning.version} deprecated: {warning.message}",
        category=DeprecationWarning,
        stacklevel=2
    )