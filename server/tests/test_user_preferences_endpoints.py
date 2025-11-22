"""
Tests for user preferences API endpoints.
"""

import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.crud.user_preferences import UserPreferencesCRUD
from app.api.v1.endpoints.user_preferences import get_user_preferences_crud


# ==================== FIXTURES ====================

@pytest.fixture
def test_pref_user_id() -> UUID:
    """Fixture for a test user ID."""
    return uuid4()


@pytest.fixture
def test_tag_id() -> int:
    """Fixture for a test tag ID."""
    return 1


@pytest.fixture
def test_preference_data(test_pref_user_id: UUID, test_tag_id: int):
    """Fixture for test preference data."""
    return {
        "uid": test_pref_user_id,
        "tag_id": test_tag_id,
    }


@pytest.fixture
def test_preferences_list(test_pref_user_id: UUID):
    """Fixture for a list of test preferences."""
    return [
        {"uid": test_pref_user_id, "tag_id": 1},
        {"uid": test_pref_user_id, "tag_id": 2},
        {"uid": test_pref_user_id, "tag_id": 3},
    ]


@pytest.fixture
def test_preferences_with_tags(test_pref_user_id: UUID):
    """Fixture for preferences with tag details."""
    return [
        {
            "uid": test_pref_user_id,
            "tag_id": 1,
            "tags": {"id": 1, "name": "Python"},
        },
        {
            "uid": test_pref_user_id,
            "tag_id": 2,
            "tags": {"id": 2, "name": "JavaScript"},
        },
    ]


@pytest.fixture
def mock_user_preferences_crud(mock_supabase_client):
    """Fixture for a mock UserPreferencesCRUD instance."""
    return UserPreferencesCRUD(mock_supabase_client)


@pytest.fixture
def prefs_client(mock_user_preferences_crud: UserPreferencesCRUD):
    """Fixture for FastAPI test client with mocked user preferences dependencies."""
    
    def override_get_user_preferences_crud():
        return mock_user_preferences_crud
    
    app.dependency_overrides[get_user_preferences_crud] = override_get_user_preferences_crud
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ==================== ADD SINGLE PREFERENCE TESTS ====================

class TestAddPreference:
    """Tests for POST /user-preferences/ endpoint."""

    @pytest.mark.asyncio
    async def test_add_preference_success(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_tag_id, test_preference_data
    ):
        """Test successfully adding a single preference."""
        mock_user_preferences_crud.add_preference = AsyncMock(return_value=test_preference_data)
        
        payload = {
            "uid": str(test_pref_user_id),
            "tag_id": test_tag_id,
        }
        
        response = prefs_client.post("/api/v1/user-preferences/", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["uid"] == str(test_pref_user_id)
        assert data["tag_id"] == test_tag_id
        mock_user_preferences_crud.add_preference.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_preference_failure(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_tag_id
    ):
        """Test failed preference addition (duplicate or invalid tag)."""
        mock_user_preferences_crud.add_preference = AsyncMock(return_value=None)
        
        payload = {
            "uid": str(test_pref_user_id),
            "tag_id": test_tag_id,
        }
        
        response = prefs_client.post("/api/v1/user-preferences/", json=payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "failed" in response.json()["detail"].lower()


# ==================== ADD BULK PREFERENCES TESTS ====================

class TestAddPreferencesBulk:
    """Tests for POST /user-preferences/bulk endpoint."""

    @pytest.mark.asyncio
    async def test_add_preferences_bulk_success(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_preferences_list
    ):
        """Test successfully adding multiple preferences."""
        mock_user_preferences_crud.add_preferences_bulk = AsyncMock(return_value=test_preferences_list)
        
        payload = {
            "uid": str(test_pref_user_id),
            "tag_ids": [1, 2, 3],
        }
        
        response = prefs_client.post("/api/v1/user-preferences/bulk", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert all(item["uid"] == str(test_pref_user_id) for item in data)
        mock_user_preferences_crud.add_preferences_bulk.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_preferences_bulk_single_tag(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test adding bulk preferences with a single tag."""
        single_pref = [{"uid": test_pref_user_id, "tag_id": 1}]
        mock_user_preferences_crud.add_preferences_bulk = AsyncMock(return_value=single_pref)
        
        payload = {
            "uid": str(test_pref_user_id),
            "tag_ids": [1],
        }
        
        response = prefs_client.post("/api/v1/user-preferences/bulk", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_add_preferences_bulk_failure(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test failed bulk preference addition."""
        mock_user_preferences_crud.add_preferences_bulk = AsyncMock(return_value=None)
        
        payload = {
            "uid": str(test_pref_user_id),
            "tag_ids": [1, 2, 3],
        }
        
        response = prefs_client.post("/api/v1/user-preferences/bulk", json=payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== GET USER PREFERENCES TESTS ====================

class TestGetUserPreferences:
    """Tests for GET /user-preferences/user/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_preferences_success(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_preferences_list
    ):
        """Test successfully getting user preferences."""
        mock_user_preferences_crud.get_user_preferences = AsyncMock(return_value=test_preferences_list)
        
        response = prefs_client.get(f"/api/v1/user-preferences/user/{test_pref_user_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        mock_user_preferences_crud.get_user_preferences.assert_called_once_with(test_pref_user_id)

    @pytest.mark.asyncio
    async def test_get_user_preferences_empty(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test getting preferences for user with no preferences."""
        mock_user_preferences_crud.get_user_preferences = AsyncMock(return_value=[])
        
        response = prefs_client.get(f"/api/v1/user-preferences/user/{test_pref_user_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


# ==================== GET PREFERENCES WITH TAGS TESTS ====================

class TestGetUserPreferencesWithTags:
    """Tests for GET /user-preferences/user/{user_id}/with-tags endpoint."""

    @pytest.mark.asyncio
    async def test_get_preferences_with_tags_success(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_preferences_with_tags
    ):
        """Test successfully getting preferences with tag details."""
        mock_user_preferences_crud.get_user_preferences_with_tags = AsyncMock(
            return_value=test_preferences_with_tags
        )
        
        response = prefs_client.get(f"/api/v1/user-preferences/user/{test_pref_user_id}/with-tags")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert "tags" in data[0]
        mock_user_preferences_crud.get_user_preferences_with_tags.assert_called_once_with(test_pref_user_id)

    @pytest.mark.asyncio
    async def test_get_preferences_with_tags_empty(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test getting preferences with tags for user with no preferences."""
        mock_user_preferences_crud.get_user_preferences_with_tags = AsyncMock(return_value=[])
        
        response = prefs_client.get(f"/api/v1/user-preferences/user/{test_pref_user_id}/with-tags")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


# ==================== GET USER TAG IDS TESTS ====================

class TestGetUserTagIds:
    """Tests for GET /user-preferences/user/{user_id}/tag-ids endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_tag_ids_success(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test successfully getting user's tag IDs."""
        mock_user_preferences_crud.get_user_tag_ids = AsyncMock(return_value=[1, 2, 3])
        
        response = prefs_client.get(f"/api/v1/user-preferences/user/{test_pref_user_id}/tag-ids")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == [1, 2, 3]
        mock_user_preferences_crud.get_user_tag_ids.assert_called_once_with(test_pref_user_id)

    @pytest.mark.asyncio
    async def test_get_user_tag_ids_empty(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test getting tag IDs for user with no preferences."""
        mock_user_preferences_crud.get_user_tag_ids = AsyncMock(return_value=[])
        
        response = prefs_client.get(f"/api/v1/user-preferences/user/{test_pref_user_id}/tag-ids")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


# ==================== HAS PREFERENCE TESTS ====================

class TestHasPreference:
    """Tests for GET /user-preferences/user/{user_id}/has/{tag_id} endpoint."""

    @pytest.mark.asyncio
    async def test_has_preference_true(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_tag_id
    ):
        """Test checking for existing preference."""
        mock_user_preferences_crud.has_preference = AsyncMock(return_value=True)
        
        response = prefs_client.get(
            f"/api/v1/user-preferences/user/{test_pref_user_id}/has/{test_tag_id}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() is True
        mock_user_preferences_crud.has_preference.assert_called_once_with(test_pref_user_id, test_tag_id)

    @pytest.mark.asyncio
    async def test_has_preference_false(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_tag_id
    ):
        """Test checking for non-existing preference."""
        mock_user_preferences_crud.has_preference = AsyncMock(return_value=False)
        
        response = prefs_client.get(
            f"/api/v1/user-preferences/user/{test_pref_user_id}/has/{test_tag_id}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() is False


# ==================== REMOVE PREFERENCE TESTS ====================

class TestRemovePreference:
    """Tests for DELETE /user-preferences/user/{user_id}/tag/{tag_id} endpoint."""

    @pytest.mark.asyncio
    async def test_remove_preference_success(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_tag_id
    ):
        """Test successfully removing a preference."""
        mock_user_preferences_crud.remove_preference = AsyncMock(return_value=True)
        
        response = prefs_client.delete(
            f"/api/v1/user-preferences/user/{test_pref_user_id}/tag/{test_tag_id}"
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_user_preferences_crud.remove_preference.assert_called_once_with(test_pref_user_id, test_tag_id)

    @pytest.mark.asyncio
    async def test_remove_preference_not_found(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_tag_id
    ):
        """Test removing non-existent preference."""
        mock_user_preferences_crud.remove_preference = AsyncMock(return_value=False)
        
        response = prefs_client.delete(
            f"/api/v1/user-preferences/user/{test_pref_user_id}/tag/{test_tag_id}"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


# ==================== REMOVE ALL PREFERENCES TESTS ====================

class TestRemoveAllPreferences:
    """Tests for DELETE /user-preferences/user/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_remove_all_preferences_success(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test successfully removing all preferences."""
        mock_user_preferences_crud.remove_all_preferences = AsyncMock(return_value=True)
        
        response = prefs_client.delete(f"/api/v1/user-preferences/user/{test_pref_user_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_user_preferences_crud.remove_all_preferences.assert_called_once_with(test_pref_user_id)

    @pytest.mark.asyncio
    async def test_remove_all_preferences_not_found(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test removing all preferences for user with no preferences."""
        mock_user_preferences_crud.remove_all_preferences = AsyncMock(return_value=False)
        
        response = prefs_client.delete(f"/api/v1/user-preferences/user/{test_pref_user_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "no preferences found" in response.json()["detail"].lower()


# ==================== SET PREFERENCES TESTS ====================

class TestSetPreferences:
    """Tests for PUT /user-preferences/user/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_set_preferences_success(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id, test_preferences_list
    ):
        """Test successfully setting (replacing) preferences."""
        mock_user_preferences_crud.set_preferences = AsyncMock(return_value=test_preferences_list)
        
        payload = [1, 2, 3]
        
        response = prefs_client.put(
            f"/api/v1/user-preferences/user/{test_pref_user_id}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        mock_user_preferences_crud.set_preferences.assert_called_once_with(test_pref_user_id, [1, 2, 3])

    @pytest.mark.asyncio
    async def test_set_preferences_empty_list(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test setting empty preferences (clear all)."""
        mock_user_preferences_crud.set_preferences = AsyncMock(return_value=[])
        
        payload = []
        
        response = prefs_client.put(
            f"/api/v1/user-preferences/user/{test_pref_user_id}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_set_preferences_single_tag(
        self, prefs_client, mock_user_preferences_crud, test_pref_user_id
    ):
        """Test setting a single preference."""
        single_pref = [{"uid": test_pref_user_id, "tag_id": 1}]
        mock_user_preferences_crud.set_preferences = AsyncMock(return_value=single_pref)
        
        payload = [1]
        
        response = prefs_client.put(
            f"/api/v1/user-preferences/user/{test_pref_user_id}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1


# ==================== GET USERS BY TAG PREFERENCE TESTS ====================

class TestGetUsersByTagPreference:
    """Tests for GET /user-preferences/tag/{tag_id}/users endpoint."""

    @pytest.mark.asyncio
    async def test_get_users_by_tag_preference_success(
        self, prefs_client, mock_user_preferences_crud, test_tag_id
    ):
        """Test successfully getting users who prefer a tag."""
        users_with_pref = [
            {"uid": uuid4(), "tag_id": test_tag_id},
            {"uid": uuid4(), "tag_id": test_tag_id},
        ]
        mock_user_preferences_crud.get_users_by_tag_preference = AsyncMock(return_value=users_with_pref)
        
        response = prefs_client.get(f"/api/v1/user-preferences/tag/{test_tag_id}/users")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_user_preferences_crud.get_users_by_tag_preference.assert_called_once_with(test_tag_id, 100, 0)

    @pytest.mark.asyncio
    async def test_get_users_by_tag_preference_with_pagination(
        self, prefs_client, mock_user_preferences_crud, test_tag_id
    ):
        """Test getting users with pagination parameters."""
        users_with_pref = [{"uid": uuid4(), "tag_id": test_tag_id}]
        mock_user_preferences_crud.get_users_by_tag_preference = AsyncMock(return_value=users_with_pref)
        
        response = prefs_client.get(
            f"/api/v1/user-preferences/tag/{test_tag_id}/users?limit=10&offset=5"
        )
        
        assert response.status_code == status.HTTP_200_OK
        mock_user_preferences_crud.get_users_by_tag_preference.assert_called_once_with(test_tag_id, 10, 5)

    @pytest.mark.asyncio
    async def test_get_users_by_tag_preference_empty(
        self, prefs_client, mock_user_preferences_crud, test_tag_id
    ):
        """Test getting users for tag with no preferences."""
        mock_user_preferences_crud.get_users_by_tag_preference = AsyncMock(return_value=[])
        
        response = prefs_client.get(f"/api/v1/user-preferences/tag/{test_tag_id}/users")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


# ==================== COUNT USERS WITH PREFERENCE TESTS ====================

class TestCountUsersWithPreference:
    """Tests for GET /user-preferences/tag/{tag_id}/count endpoint."""

    @pytest.mark.asyncio
    async def test_count_users_with_preference_success(
        self, prefs_client, mock_user_preferences_crud, test_tag_id
    ):
        """Test successfully counting users with preference."""
        mock_user_preferences_crud.count_users_with_preference = AsyncMock(return_value=42)
        
        response = prefs_client.get(f"/api/v1/user-preferences/tag/{test_tag_id}/count")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == 42
        mock_user_preferences_crud.count_users_with_preference.assert_called_once_with(test_tag_id)

    @pytest.mark.asyncio
    async def test_count_users_with_preference_zero(
        self, prefs_client, mock_user_preferences_crud, test_tag_id
    ):
        """Test counting users for tag with no preferences."""
        mock_user_preferences_crud.count_users_with_preference = AsyncMock(return_value=0)
        
        response = prefs_client.get(f"/api/v1/user-preferences/tag/{test_tag_id}/count")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == 0

    @pytest.mark.asyncio
    async def test_count_users_with_preference_large_number(
        self, prefs_client, mock_user_preferences_crud, test_tag_id
    ):
        """Test counting with large number of users."""
        mock_user_preferences_crud.count_users_with_preference = AsyncMock(return_value=10000)
        
        response = prefs_client.get(f"/api/v1/user-preferences/tag/{test_tag_id}/count")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == 10000
