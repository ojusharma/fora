"""
Tests for user API endpoints.
"""

import pytest
from uuid import uuid4, UUID
from datetime import date, datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status

from app.schemas.user import UserRole


class TestGetUser:
    """Tests for GET /users/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_success(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test successfully getting a user by ID."""
        mock_user_crud.get_user = AsyncMock(return_value=test_user_data)
        
        response = client.get(f"/api/v1/users/{test_user_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["uid"] == str(test_user_id)
        assert data["phone"] == "+1234567890"
        assert data["role"] == "user"
        assert data["credits"] == 100
        mock_user_crud.get_user.assert_called_once_with(test_user_id)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client, mock_user_crud, test_user_id):
        """Test getting a non-existent user."""
        mock_user_crud.get_user = AsyncMock(return_value=None)
        
        response = client.get(f"/api/v1/users/{test_user_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_user_normalizes_id_key(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test that response normalizes 'id' to 'uid'."""
        # Return data with 'id' instead of 'uid'
        data_with_id = test_user_data.copy()
        data_with_id["id"] = data_with_id.pop("uid")
        
        mock_user_crud.get_user = AsyncMock(return_value=data_with_id)
        
        response = client.get(f"/api/v1/users/{test_user_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "uid" in data
        assert data["uid"] == str(test_user_id)


class TestGetUsers:
    """Tests for GET /users/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_users_default_params(self, client, mock_user_crud):
        """Test getting users with default pagination."""
        users_data = [
            {"uid": uuid4(), "role": "user", "credits": 100},
            {"uid": uuid4(), "role": "admin", "credits": 200},
        ]
        mock_user_crud.get_users = AsyncMock(return_value=users_data)
        
        response = client.get("/api/v1/users/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        mock_user_crud.get_users.assert_called_once_with(skip=0, limit=100, role=None)

    @pytest.mark.asyncio
    async def test_get_users_with_pagination(self, client, mock_user_crud):
        """Test getting users with custom pagination."""
        mock_user_crud.get_users = AsyncMock(return_value=[])
        
        response = client.get("/api/v1/users/?skip=10&limit=50")
        
        assert response.status_code == status.HTTP_200_OK
        mock_user_crud.get_users.assert_called_once_with(skip=10, limit=50, role=None)

    @pytest.mark.asyncio
    async def test_get_users_filter_by_role(self, client, mock_user_crud):
        """Test filtering users by role."""
        users_data = [{"uid": uuid4(), "role": "admin", "credits": 200}]
        mock_user_crud.get_users = AsyncMock(return_value=users_data)
        
        response = client.get("/api/v1/users/?role=admin")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["role"] == "admin"
        mock_user_crud.get_users.assert_called_once_with(skip=0, limit=100, role="admin")

    @pytest.mark.asyncio
    async def test_get_users_empty_result(self, client, mock_user_crud):
        """Test getting users when none exist."""
        mock_user_crud.get_users = AsyncMock(return_value=[])
        
        response = client.get("/api/v1/users/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


class TestCreateUser:
    """Tests for POST /users/ endpoint."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, client, mock_user_crud):
        """Test successfully creating a user."""
        new_user_id = uuid4()
        user_payload = {
            "uid": str(new_user_id),
            "dob": "1990-01-01",
            "phone": "+1234567890",
            "role": "user",
            "credits": 50,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "display_name": "New User",
        }
        
        created_user = user_payload.copy()
        created_user["uid"] = new_user_id
        created_user["last_updated"] = datetime.utcnow()
        
        mock_user_crud.get_user = AsyncMock(return_value=None)
        mock_user_crud.create_user = AsyncMock(return_value=created_user)
        
        response = client.post("/api/v1/users/", json=user_payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["uid"] == str(new_user_id)
        assert data["credits"] == 50
        mock_user_crud.get_user.assert_called_once()
        mock_user_crud.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test creating a user that already exists."""
        user_payload = {
            "uid": str(test_user_id),
            "role": "user",
        }
        
        mock_user_crud.get_user = AsyncMock(return_value=test_user_data)
        
        response = client.post("/api/v1/users/", json=user_payload)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_user_with_enum_role(self, client, mock_user_crud):
        """Test creating a user with role enum."""
        new_user_id = uuid4()
        user_payload = {
            "uid": str(new_user_id),
            "role": "admin",
        }
        
        created_user = {"uid": new_user_id, "role": "admin", "credits": 0}
        
        mock_user_crud.get_user = AsyncMock(return_value=None)
        mock_user_crud.create_user = AsyncMock(return_value=created_user)
        
        response = client.post("/api/v1/users/", json=user_payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["role"] == "admin"


class TestUpdateUser:
    """Tests for PATCH /users/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_user_success(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test successfully updating a user."""
        update_payload = {
            "phone": "+9876543210",
            "display_name": "Updated Name",
        }
        
        updated_user = test_user_data.copy()
        updated_user.update(update_payload)
        
        mock_user_crud.get_user = AsyncMock(return_value=test_user_data)
        mock_user_crud.update_user = AsyncMock(return_value=updated_user)
        
        response = client.patch(f"/api/v1/users/{test_user_id}", json=update_payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["phone"] == "+9876543210"
        assert data["display_name"] == "Updated Name"
        mock_user_crud.update_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client, mock_user_crud, test_user_id):
        """Test updating a non-existent user."""
        update_payload = {"phone": "+9876543210"}
        
        mock_user_crud.get_user = AsyncMock(return_value=None)
        
        response = client.patch(f"/api/v1/users/{test_user_id}", json=update_payload)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_user_no_fields(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test updating with no fields provided."""
        mock_user_crud.get_user = AsyncMock(return_value=test_user_data)
        
        response = client.patch(f"/api/v1/users/{test_user_id}", json={})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no fields to update" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_user_partial_fields(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test partial update with only some fields."""
        update_payload = {"latitude": 51.5074}
        
        updated_user = test_user_data.copy()
        updated_user["latitude"] = 51.5074
        
        mock_user_crud.get_user = AsyncMock(return_value=test_user_data)
        mock_user_crud.update_user = AsyncMock(return_value=updated_user)
        
        response = client.patch(f"/api/v1/users/{test_user_id}", json=update_payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["latitude"] == 51.5074


class TestDeleteUser:
    """Tests for DELETE /users/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, client, mock_user_crud, test_user_id):
        """Test successfully deleting a user."""
        mock_user_crud.delete_user = AsyncMock(return_value=True)
        
        response = client.delete(f"/api/v1/users/{test_user_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_user_crud.delete_user.assert_called_once_with(test_user_id)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client, mock_user_crud, test_user_id):
        """Test deleting a non-existent user."""
        mock_user_crud.delete_user = AsyncMock(return_value=False)
        
        response = client.delete(f"/api/v1/users/{test_user_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateUserCredits:
    """Tests for PATCH /users/{user_id}/credits endpoint."""

    @pytest.mark.asyncio
    async def test_update_credits_success(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test successfully updating user credits."""
        credits_payload = {"credits": 500}
        
        updated_user = test_user_data.copy()
        updated_user["credits"] = 500
        
        mock_user_crud.update_user_credits = AsyncMock(return_value=updated_user)
        
        response = client.patch(f"/api/v1/users/{test_user_id}/credits", json=credits_payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["credits"] == 500
        mock_user_crud.update_user_credits.assert_called_once_with(test_user_id, 500)

    @pytest.mark.asyncio
    async def test_update_credits_user_not_found(self, client, mock_user_crud, test_user_id):
        """Test updating credits for non-existent user."""
        credits_payload = {"credits": 500}
        
        mock_user_crud.update_user_credits = AsyncMock(return_value=None)
        
        response = client.patch(f"/api/v1/users/{test_user_id}/credits", json=credits_payload)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAddUserCredits:
    """Tests for POST /users/{user_id}/credits/add endpoint."""

    @pytest.mark.asyncio
    async def test_add_credits_success(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test successfully adding credits."""
        updated_user = test_user_data.copy()
        updated_user["credits"] = 150  # 100 + 50
        
        mock_user_crud.add_user_credits = AsyncMock(return_value=updated_user)
        
        response = client.post(f"/api/v1/users/{test_user_id}/credits/add?amount=50")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["credits"] == 150
        mock_user_crud.add_user_credits.assert_called_once_with(test_user_id, 50)

    @pytest.mark.asyncio
    async def test_subtract_credits(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test subtracting credits with negative amount."""
        updated_user = test_user_data.copy()
        updated_user["credits"] = 70  # 100 - 30
        
        mock_user_crud.add_user_credits = AsyncMock(return_value=updated_user)
        
        response = client.post(f"/api/v1/users/{test_user_id}/credits/add?amount=-30")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["credits"] == 70
        mock_user_crud.add_user_credits.assert_called_once_with(test_user_id, -30)

    @pytest.mark.asyncio
    async def test_add_credits_user_not_found(self, client, mock_user_crud, test_user_id):
        """Test adding credits to non-existent user."""
        mock_user_crud.add_user_credits = AsyncMock(return_value=None)
        
        response = client.post(f"/api/v1/users/{test_user_id}/credits/add?amount=50")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateUserLocation:
    """Tests for PATCH /users/{user_id}/location endpoint."""

    @pytest.mark.asyncio
    async def test_update_location_success(self, client, mock_user_crud, test_user_id, test_user_data):
        """Test successfully updating user location."""
        location_payload = {
            "latitude": 51.5074,
            "longitude": -0.1278,
        }
        
        updated_user = test_user_data.copy()
        updated_user.update(location_payload)
        
        mock_user_crud.update_user_location = AsyncMock(return_value=updated_user)
        
        response = client.patch(f"/api/v1/users/{test_user_id}/location", json=location_payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["latitude"] == 51.5074
        assert data["longitude"] == -0.1278
        mock_user_crud.update_user_location.assert_called_once_with(
            test_user_id, 51.5074, -0.1278
        )

    @pytest.mark.asyncio
    async def test_update_location_invalid_coordinates(self, client, mock_user_crud, test_user_id):
        """Test updating with invalid coordinates."""
        location_payload = {
            "latitude": 91.0,  # Invalid: > 90
            "longitude": -0.1278,
        }
        
        response = client.patch(f"/api/v1/users/{test_user_id}/location", json=location_payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_location_user_not_found(self, client, mock_user_crud, test_user_id):
        """Test updating location for non-existent user."""
        location_payload = {
            "latitude": 51.5074,
            "longitude": -0.1278,
        }
        
        mock_user_crud.update_user_location = AsyncMock(return_value=None)
        
        response = client.patch(f"/api/v1/users/{test_user_id}/location", json=location_payload)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetNearbyUsers:
    """Tests for GET /users/nearby/search endpoint."""

    @pytest.mark.asyncio
    async def test_get_nearby_users_success(self, client, mock_user_crud):
        """Test successfully finding nearby users."""
        nearby_users = [
            {
                "uid": uuid4(),
                "latitude": 40.7589,
                "longitude": -73.9851,
                "distance_km": 5.2,
            },
            {
                "uid": uuid4(),
                "latitude": 40.7489,
                "longitude": -73.9680,
                "distance_km": 8.7,
            },
        ]
        
        mock_user_crud.get_users_by_location = AsyncMock(return_value=nearby_users)
        
        response = client.get(
            "/api/v1/users/nearby/search?latitude=40.7128&longitude=-74.0060&radius_km=10"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        mock_user_crud.get_users_by_location.assert_called_once_with(
            latitude=40.7128, longitude=-74.0060, radius_km=10.0, limit=50
        )

    @pytest.mark.asyncio
    async def test_get_nearby_users_with_limit(self, client, mock_user_crud):
        """Test finding nearby users with custom limit."""
        mock_user_crud.get_users_by_location = AsyncMock(return_value=[])
        
        response = client.get(
            "/api/v1/users/nearby/search?latitude=40.7128&longitude=-74.0060&radius_km=20&limit=100"
        )
        
        assert response.status_code == status.HTTP_200_OK
        mock_user_crud.get_users_by_location.assert_called_once_with(
            latitude=40.7128, longitude=-74.0060, radius_km=20.0, limit=100
        )

    @pytest.mark.asyncio
    async def test_get_nearby_users_no_results(self, client, mock_user_crud):
        """Test finding nearby users with no results."""
        mock_user_crud.get_users_by_location = AsyncMock(return_value=[])
        
        response = client.get(
            "/api/v1/users/nearby/search?latitude=40.7128&longitude=-74.0060"
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_nearby_users_invalid_params(self, client, mock_user_crud):
        """Test nearby search with invalid parameters."""
        response = client.get(
            "/api/v1/users/nearby/search?latitude=91&longitude=-74.0060"
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCheckUserExists:
    """Tests for GET /users/{user_id}/exists endpoint."""

    @pytest.mark.asyncio
    async def test_user_exists_true(self, client, mock_user_crud, test_user_id):
        """Test checking if user exists (returns true)."""
        mock_user_crud.user_exists = AsyncMock(return_value=True)
        
        response = client.get(f"/api/v1/users/{test_user_id}/exists")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["exists"] is True
        assert data["user_id"] == str(test_user_id)
        mock_user_crud.user_exists.assert_called_once_with(test_user_id)

    @pytest.mark.asyncio
    async def test_user_exists_false(self, client, mock_user_crud, test_user_id):
        """Test checking if user exists (returns false)."""
        mock_user_crud.user_exists = AsyncMock(return_value=False)
        
        response = client.get(f"/api/v1/users/{test_user_id}/exists")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["exists"] is False
        assert data["user_id"] == str(test_user_id)
