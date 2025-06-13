import pytest
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

@pytest.fixture
def mock_user_data() -> Dict[str, Any]:
    """Mock user data for testing."""
    return {
        "id": str(uuid4()),
        "auth0_id": "auth0|test123",
        "email": "test@example.com",
        "full_name": "Test User",
        "native_language": "english",
        "industry_id": str(uuid4()),
        "selected_role_id": str(uuid4()),
        "custom_role_title": None,
        "custom_role_description": None,
        "onboarding_status": "personalisation",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_industry_data() -> Dict[str, Any]:
    """Mock industry data for testing."""
    return {
        "id": str(uuid4()),
        "name": "Banking & Finance",
        "status": "available",
        "sort_order": 1,
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_role_data() -> Dict[str, Any]:
    """Mock role data for testing."""
    return {
        "id": str(uuid4()),
        "title": "Financial Analyst",
        "description": "Analyzes financial data and provides insights to stakeholders",
        "industry_id": str(uuid4()),
        "is_system_role": True,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_communication_partner_data() -> Dict[str, Any]:
    """Mock communication partner data for testing."""
    return {
        "id": str(uuid4()),
        "name": "Clients",
        "description": "External clients and customers",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_situation_data() -> Dict[str, Any]:
    """Mock situation/unit data for testing."""
    return {
        "id": str(uuid4()),
        "name": "Meetings",
        "description": "Face-to-face or virtual meetings",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }