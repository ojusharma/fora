"""
Tests for user stats API endpoints.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.crud.user_stats import UserStatsCRUD
from app.api.v1.endpoints.user_stats import get_user_stats_crud


# ==================== FIXTURES ====================

@pytest.fixture
def test_stats_user_id() -> UUID:
    """Fixture for a test user ID."""
    return uuid4()


@pytest.fixture
def test_user_stats_data(test_stats_user_id: UUID):
    """Fixture for test user stats data."""
    return {
        "uid": test_stats_user_id,
        "num_listings_posted": 5,
        "num_listings_applied": 10,
        "num_listings_assigned": 3,
        "num_listings_completed": 2,
        "avg_rating": 4.5,
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def mock_user_stats_crud(mock_supabase_client):
    """Fixture for a mock UserStatsCRUD instance."""
    return UserStatsCRUD(mock_supabase_client)


@pytest.fixture
def stats_client(mock_user_stats_crud: UserStatsCRUD):
    """Fixture for FastAPI test client with mocked user stats dependencies."""
    
    def override_get_user_stats_crud():
        return mock_user_stats_crud
    
    app.dependency_overrides[get_user_stats_crud] = override_get_user_stats_crud
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ==================== CREATE USER STATS TESTS ====================

class TestCreateUserStats:
    """Tests for POST /user-stats/ endpoint."""

    @pytest.mark.asyncio
    async def test_create_user_stats_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test successfully creating user stats."""
        mock_user_stats_crud.create_user_stats = AsyncMock(return_value=test_user_stats_data)
        
        payload = {
            "uid": str(test_stats_user_id),
            "num_listings_posted": 5,
            "num_listings_applied": 10,
            "num_listings_assigned": 3,
            "num_listings_completed": 2,
            "avg_rating": 4.5,
        }
        
        response = stats_client.post("/api/v1/user-stats/", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["uid"] == str(test_stats_user_id)
        assert data["num_listings_posted"] == 5
        assert float(data["avg_rating"]) == 4.5
        mock_user_stats_crud.create_user_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_stats_with_defaults(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test creating user stats with default values."""
        default_stats = {
            "uid": test_stats_user_id,
            "num_listings_posted": 0,
            "num_listings_applied": 0,
            "num_listings_assigned": 0,
            "num_listings_completed": 0,
            "avg_rating": None,
            "updated_at": datetime.utcnow().isoformat(),
        }
        mock_user_stats_crud.create_user_stats = AsyncMock(return_value=default_stats)
        
        payload = {"uid": str(test_stats_user_id)}
        
        response = stats_client.post("/api/v1/user-stats/", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["num_listings_posted"] == 0
        assert data["avg_rating"] is None

    @pytest.mark.asyncio
    async def test_create_user_stats_failure(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test failed user stats creation."""
        mock_user_stats_crud.create_user_stats = AsyncMock(return_value=None)
        
        payload = {"uid": str(test_stats_user_id)}
        
        response = stats_client.post("/api/v1/user-stats/", json=payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "failed" in response.json()["detail"].lower()


# ==================== GET USER STATS TESTS ====================

class TestGetUserStats:
    """Tests for GET /user-stats/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_stats_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test successfully getting user stats."""
        mock_user_stats_crud.get_user_stats = AsyncMock(return_value=test_user_stats_data)
        
        response = stats_client.get(f"/api/v1/user-stats/{test_stats_user_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["uid"] == str(test_stats_user_id)
        assert data["num_listings_posted"] == 5
        assert float(data["avg_rating"]) == 4.5
        mock_user_stats_crud.get_user_stats.assert_called_once_with(test_stats_user_id)

    @pytest.mark.asyncio
    async def test_get_user_stats_not_found(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test getting non-existent user stats."""
        mock_user_stats_crud.get_user_stats = AsyncMock(return_value=None)
        
        response = stats_client.get(f"/api/v1/user-stats/{test_stats_user_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


# ==================== GET OR CREATE USER STATS TESTS ====================

class TestGetOrCreateUserStats:
    """Tests for GET /user-stats/{user_id}/or-create endpoint."""

    @pytest.mark.asyncio
    async def test_get_or_create_existing_stats(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test getting existing user stats."""
        mock_user_stats_crud.get_or_create_user_stats = AsyncMock(return_value=test_user_stats_data)
        
        response = stats_client.get(f"/api/v1/user-stats/{test_stats_user_id}/or-create")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["uid"] == str(test_stats_user_id)
        mock_user_stats_crud.get_or_create_user_stats.assert_called_once_with(test_stats_user_id)

    @pytest.mark.asyncio
    async def test_get_or_create_new_stats(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test creating new user stats when they don't exist."""
        new_stats = {
            "uid": test_stats_user_id,
            "num_listings_posted": 0,
            "num_listings_applied": 0,
            "num_listings_assigned": 0,
            "num_listings_completed": 0,
            "avg_rating": None,
            "updated_at": datetime.utcnow().isoformat(),
        }
        mock_user_stats_crud.get_or_create_user_stats = AsyncMock(return_value=new_stats)
        
        response = stats_client.get(f"/api/v1/user-stats/{test_stats_user_id}/or-create")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["uid"] == str(test_stats_user_id)
        assert data["num_listings_posted"] == 0


# ==================== UPDATE USER STATS TESTS ====================

class TestUpdateUserStats:
    """Tests for PATCH /user-stats/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_user_stats_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test successfully updating user stats."""
        updated_data = test_user_stats_data.copy()
        updated_data["num_listings_posted"] = 10
        mock_user_stats_crud.update_user_stats = AsyncMock(return_value=updated_data)
        
        payload = {"num_listings_posted": 10}
        
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}", json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["num_listings_posted"] == 10
        mock_user_stats_crud.update_user_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_stats_partial(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test partial update of user stats."""
        updated_data = test_user_stats_data.copy()
        updated_data["avg_rating"] = 4.8
        mock_user_stats_crud.update_user_stats = AsyncMock(return_value=updated_data)
        
        payload = {"avg_rating": 4.8}
        
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}", json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["avg_rating"]) == 4.8

    @pytest.mark.asyncio
    async def test_update_user_stats_not_found(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test updating non-existent user stats."""
        mock_user_stats_crud.update_user_stats = AsyncMock(return_value=None)
        
        payload = {"num_listings_posted": 10}
        
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}", json=payload
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


# ==================== DELETE USER STATS TESTS ====================

class TestDeleteUserStats:
    """Tests for DELETE /user-stats/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_user_stats_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test successfully deleting user stats."""
        mock_user_stats_crud.delete_user_stats = AsyncMock(return_value=True)
        
        response = stats_client.delete(f"/api/v1/user-stats/{test_stats_user_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_user_stats_crud.delete_user_stats.assert_called_once_with(test_stats_user_id)

    @pytest.mark.asyncio
    async def test_delete_user_stats_not_found(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test deleting non-existent user stats."""
        mock_user_stats_crud.delete_user_stats = AsyncMock(return_value=False)
        
        response = stats_client.delete(f"/api/v1/user-stats/{test_stats_user_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


# ==================== INCREMENT OPERATIONS TESTS ====================

class TestIncrementListingsPosted:
    """Tests for POST /user-stats/{user_id}/increment/listings-posted endpoint."""

    @pytest.mark.asyncio
    async def test_increment_listings_posted_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test successfully incrementing listings posted."""
        updated_data = test_user_stats_data.copy()
        updated_data["num_listings_posted"] = 6
        mock_user_stats_crud.increment_listings_posted = AsyncMock(return_value=updated_data)
        
        response = stats_client.post(
            f"/api/v1/user-stats/{test_stats_user_id}/increment/listings-posted"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["num_listings_posted"] == 6
        mock_user_stats_crud.increment_listings_posted.assert_called_once_with(test_stats_user_id)

    @pytest.mark.asyncio
    async def test_increment_listings_posted_not_found(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test incrementing listings posted for non-existent user."""
        mock_user_stats_crud.increment_listings_posted = AsyncMock(return_value=None)
        
        response = stats_client.post(
            f"/api/v1/user-stats/{test_stats_user_id}/increment/listings-posted"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestIncrementListingsApplied:
    """Tests for POST /user-stats/{user_id}/increment/listings-applied endpoint."""

    @pytest.mark.asyncio
    async def test_increment_listings_applied_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test successfully incrementing listings applied."""
        updated_data = test_user_stats_data.copy()
        updated_data["num_listings_applied"] = 11
        mock_user_stats_crud.increment_listings_applied = AsyncMock(return_value=updated_data)
        
        response = stats_client.post(
            f"/api/v1/user-stats/{test_stats_user_id}/increment/listings-applied"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["num_listings_applied"] == 11
        mock_user_stats_crud.increment_listings_applied.assert_called_once_with(test_stats_user_id)

    @pytest.mark.asyncio
    async def test_increment_listings_applied_not_found(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test incrementing listings applied for non-existent user."""
        mock_user_stats_crud.increment_listings_applied = AsyncMock(return_value=None)
        
        response = stats_client.post(
            f"/api/v1/user-stats/{test_stats_user_id}/increment/listings-applied"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestIncrementListingsAssigned:
    """Tests for POST /user-stats/{user_id}/increment/listings-assigned endpoint."""

    @pytest.mark.asyncio
    async def test_increment_listings_assigned_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test successfully incrementing listings assigned."""
        updated_data = test_user_stats_data.copy()
        updated_data["num_listings_assigned"] = 4
        mock_user_stats_crud.increment_listings_assigned = AsyncMock(return_value=updated_data)
        
        response = stats_client.post(
            f"/api/v1/user-stats/{test_stats_user_id}/increment/listings-assigned"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["num_listings_assigned"] == 4
        mock_user_stats_crud.increment_listings_assigned.assert_called_once_with(test_stats_user_id)

    @pytest.mark.asyncio
    async def test_increment_listings_assigned_not_found(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test incrementing listings assigned for non-existent user."""
        mock_user_stats_crud.increment_listings_assigned = AsyncMock(return_value=None)
        
        response = stats_client.post(
            f"/api/v1/user-stats/{test_stats_user_id}/increment/listings-assigned"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestIncrementListingsCompleted:
    """Tests for POST /user-stats/{user_id}/increment/listings-completed endpoint."""

    @pytest.mark.asyncio
    async def test_increment_listings_completed_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test successfully incrementing listings completed."""
        updated_data = test_user_stats_data.copy()
        updated_data["num_listings_completed"] = 3
        mock_user_stats_crud.increment_listings_completed = AsyncMock(return_value=updated_data)
        
        response = stats_client.post(
            f"/api/v1/user-stats/{test_stats_user_id}/increment/listings-completed"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["num_listings_completed"] == 3
        mock_user_stats_crud.increment_listings_completed.assert_called_once_with(test_stats_user_id)

    @pytest.mark.asyncio
    async def test_increment_listings_completed_not_found(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test incrementing listings completed for non-existent user."""
        mock_user_stats_crud.increment_listings_completed = AsyncMock(return_value=None)
        
        response = stats_client.post(
            f"/api/v1/user-stats/{test_stats_user_id}/increment/listings-completed"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== UPDATE AVERAGE RATING TESTS ====================

class TestUpdateAvgRating:
    """Tests for PATCH /user-stats/{user_id}/rating endpoint."""

    @pytest.mark.asyncio
    async def test_update_avg_rating_success(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test successfully updating average rating."""
        updated_data = test_user_stats_data.copy()
        updated_data["avg_rating"] = 4.8
        mock_user_stats_crud.update_avg_rating = AsyncMock(return_value=updated_data)
        
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}/rating?new_rating=4.8"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["avg_rating"]) == 4.8
        mock_user_stats_crud.update_avg_rating.assert_called_once_with(test_stats_user_id, 4.8)

    @pytest.mark.asyncio
    async def test_update_avg_rating_minimum_value(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test updating rating with minimum value (0)."""
        updated_data = test_user_stats_data.copy()
        updated_data["avg_rating"] = 0.0
        mock_user_stats_crud.update_avg_rating = AsyncMock(return_value=updated_data)
        
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}/rating?new_rating=0"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["avg_rating"]) == 0.0

    @pytest.mark.asyncio
    async def test_update_avg_rating_maximum_value(
        self, stats_client, mock_user_stats_crud, test_stats_user_id, test_user_stats_data
    ):
        """Test updating rating with maximum value (5)."""
        updated_data = test_user_stats_data.copy()
        updated_data["avg_rating"] = 5.0
        mock_user_stats_crud.update_avg_rating = AsyncMock(return_value=updated_data)
        
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}/rating?new_rating=5"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["avg_rating"]) == 5.0

    @pytest.mark.asyncio
    async def test_update_avg_rating_invalid_too_low(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test updating rating with value below minimum."""
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}/rating?new_rating=-1"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "between 0 and 5" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_avg_rating_invalid_too_high(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test updating rating with value above maximum."""
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}/rating?new_rating=6"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "between 0 and 5" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_avg_rating_not_found(
        self, stats_client, mock_user_stats_crud, test_stats_user_id
    ):
        """Test updating rating for non-existent user stats."""
        mock_user_stats_crud.update_avg_rating = AsyncMock(return_value=None)
        
        response = stats_client.patch(
            f"/api/v1/user-stats/{test_stats_user_id}/rating?new_rating=4.5"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
