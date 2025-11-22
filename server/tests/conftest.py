"""
Pytest configuration and fixtures.
"""

import pytest
from typing import Generator, Dict, Any
from uuid import uuid4, UUID
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.crud.user import UserCRUD
from app.api.v1.endpoints.user import get_user_crud


# ==================== FIXTURES ====================


@pytest.fixture
def test_user_id() -> UUID:
    """Fixture for a test user ID."""
    return uuid4()


@pytest.fixture
def test_user_data(test_user_id: UUID) -> Dict[str, Any]:
    """Fixture for test user data."""
    return {
        "uid": test_user_id,
        "dob": date(1990, 1, 1),
        "phone": "+1234567890",
        "role": "user",
        "credits": 100,
        "last_updated": datetime.utcnow(),
        "latitude": 40.7128,
        "longitude": -74.0060,
        "display_name": "Test User",
    }


@pytest.fixture
def mock_supabase_client():
    """Fixture for a mock Supabase client."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    return mock_client


@pytest.fixture
def mock_user_crud(mock_supabase_client):
    """Fixture for a mock UserCRUD instance."""
    return UserCRUD(mock_supabase_client)


@pytest.fixture
def client(mock_user_crud: UserCRUD) -> Generator:
    """Fixture for FastAPI test client with mocked dependencies."""
    
    def override_get_user_crud():
        return mock_user_crud
    
    app.dependency_overrides[get_user_crud] = override_get_user_crud
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_response_success():
    """Fixture for successful Supabase response."""
    mock_response = MagicMock()
    mock_response.data = []
    return mock_response


@pytest.fixture
def mock_response_empty():
    """Fixture for empty Supabase response."""
    mock_response = MagicMock()
    mock_response.data = []
    return mock_response
