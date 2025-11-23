"""
Tests for listing API endpoints.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.crud.listing import ListingCRUD
from app.api.v1.endpoints.listings import get_listing_crud
from app.schemas.listing import ListingStatus, ApplicantStatus


# ==================== FIXTURES ====================

@pytest.fixture
def test_listing_id() -> UUID:
    """Fixture for a test listing ID."""
    return uuid4()


@pytest.fixture
def test_poster_uid() -> UUID:
    """Fixture for a test poster user ID."""
    return uuid4()


@pytest.fixture
def test_applicant_uid() -> UUID:
    """Fixture for a test applicant user ID."""
    return uuid4()


@pytest.fixture
def test_listing_data(test_listing_id: UUID, test_poster_uid: UUID):
    """Fixture for test listing data."""
    return {
        "id": test_listing_id,
        "name": "Test Listing",
        "description": "Test description",
        "images": ["image1.jpg", "image2.jpg"],
        "tags": [1, 2, 3],
        "location_address": "123 Test St",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "compensation": 100.0,
        "poster_uid": test_poster_uid,
        "assignee_uid": None,
        "applicants": [],
        "status": "open",
        "last_posted": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "poster_rating": None,
        "assignee_rating": None,
    }


@pytest.fixture
def test_listings_list(test_poster_uid: UUID):
    """Fixture for a list of test listings."""
    return [
        {
            "id": uuid4(),
            "name": "Listing 1",
            "poster_uid": test_poster_uid,
            "status": "open",
            "compensation": 50.0,
            "last_posted": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "applicants": [],
        },
        {
            "id": uuid4(),
            "name": "Listing 2",
            "poster_uid": test_poster_uid,
            "status": "in_progress",
            "compensation": 75.0,
            "last_posted": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "applicants": [],
        },
    ]


@pytest.fixture
def test_applicant_data(test_listing_id: UUID, test_applicant_uid: UUID):
    """Fixture for test applicant data."""
    return {
        "listing_id": test_listing_id,
        "applicant_uid": test_applicant_uid,
        "applied_at": datetime.utcnow().isoformat(),
        "status": "applied",
        "message": "I'm interested in this listing",
    }


@pytest.fixture
def mock_listing_crud(mock_supabase_client):
    """Fixture for a mock ListingCRUD instance."""
    return ListingCRUD(mock_supabase_client)


@pytest.fixture
def listings_client(mock_listing_crud: ListingCRUD):
    """Fixture for FastAPI test client with mocked listing dependencies."""
    
    def override_get_listing_crud():
        return mock_listing_crud
    
    app.dependency_overrides[get_listing_crud] = override_get_listing_crud
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ==================== CREATE LISTING TESTS ====================

class TestCreateListing:
    """Tests for POST /listings/ endpoint."""

    @pytest.mark.asyncio
    async def test_create_listing_success(
        self, listings_client, mock_listing_crud, test_poster_uid, test_listing_data
    ):
        """Test successfully creating a listing."""
        mock_listing_crud.create_listing = AsyncMock(return_value=test_listing_data)
        
        payload = {
            "name": "Test Listing",
            "description": "Test description",
            "images": ["image1.jpg", "image2.jpg"],
            "tags": [1, 2, 3],
            "location_address": "123 Test St",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "compensation": 100.0,
        }
        
        response = listings_client.post(
            f"/api/v1/listings/?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Listing"
        assert data["poster_uid"] == str(test_poster_uid)
        assert data["status"] == "open"
        mock_listing_crud.create_listing.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_listing_minimal(
        self, listings_client, mock_listing_crud, test_poster_uid, test_listing_id
    ):
        """Test creating a listing with minimal required fields."""
        minimal_listing = {
            "id": test_listing_id,
            "name": "Minimal Listing",
            "poster_uid": test_poster_uid,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_posted": datetime.utcnow().isoformat(),
            "applicants": [],
        }
        mock_listing_crud.create_listing = AsyncMock(return_value=minimal_listing)
        
        payload = {"name": "Minimal Listing"}
        
        response = listings_client.post(
            f"/api/v1/listings/?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Minimal Listing"

    @pytest.mark.asyncio
    async def test_create_listing_failure(
        self, listings_client, mock_listing_crud, test_poster_uid
    ):
        """Test failed listing creation."""
        mock_listing_crud.create_listing = AsyncMock(return_value=None)
        
        payload = {"name": "Test Listing"}
        
        response = listings_client.post(
            f"/api/v1/listings/?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== GET LISTINGS TESTS ====================

class TestGetListings:
    """Tests for GET /listings/ endpoint."""

    @pytest.mark.asyncio
    async def test_get_listings_success(
        self, listings_client, mock_listing_crud, test_listings_list
    ):
        """Test successfully getting listings."""
        mock_listing_crud.get_listings = AsyncMock(return_value=test_listings_list)
        
        response = listings_client.get("/api/v1/listings/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_listing_crud.get_listings.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_listings_with_filters(
        self, listings_client, mock_listing_crud, test_listings_list
    ):
        """Test getting listings with filters."""
        mock_listing_crud.get_listings = AsyncMock(return_value=test_listings_list)
        
        response = listings_client.get(
            "/api/v1/listings/?status=open&min_compensation=50&limit=10"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_listings_empty(
        self, listings_client, mock_listing_crud
    ):
        """Test getting listings when none exist."""
        mock_listing_crud.get_listings = AsyncMock(return_value=[])
        
        response = listings_client.get("/api/v1/listings/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_listings_pagination(
        self, listings_client, mock_listing_crud, test_listings_list
    ):
        """Test getting listings with pagination."""
        mock_listing_crud.get_listings = AsyncMock(return_value=test_listings_list)
        
        response = listings_client.get("/api/v1/listings/?limit=10&offset=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


# ==================== GET LISTING BY ID TESTS ====================

class TestGetListing:
    """Tests for GET /listings/{listing_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_listing_success(
        self, listings_client, mock_listing_crud, test_listing_id, test_listing_data
    ):
        """Test successfully getting a listing by ID."""
        mock_listing_crud.get_listing = AsyncMock(return_value=test_listing_data)
        
        response = listings_client.get(f"/api/v1/listings/{test_listing_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_listing_id)
        assert data["name"] == "Test Listing"
        mock_listing_crud.get_listing.assert_called_once_with(test_listing_id)

    @pytest.mark.asyncio
    async def test_get_listing_not_found(
        self, listings_client, mock_listing_crud, test_listing_id
    ):
        """Test getting a non-existent listing."""
        mock_listing_crud.get_listing = AsyncMock(return_value=None)
        
        response = listings_client.get(f"/api/v1/listings/{test_listing_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


# ==================== UPDATE LISTING TESTS ====================

class TestUpdateListing:
    """Tests for PATCH /listings/{listing_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_listing_success(
        self, listings_client, mock_listing_crud, test_listing_id, test_poster_uid, test_listing_data
    ):
        """Test successfully updating a listing."""
        updated_data = test_listing_data.copy()
        updated_data["name"] = "Updated Listing"
        mock_listing_crud.update_listing = AsyncMock(return_value=updated_data)
        
        payload = {"name": "Updated Listing"}
        
        response = listings_client.patch(
            f"/api/v1/listings/{test_listing_id}?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Listing"
        mock_listing_crud.update_listing.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_listing_partial(
        self, listings_client, mock_listing_crud, test_listing_id, test_poster_uid, test_listing_data
    ):
        """Test partial update of listing."""
        updated_data = test_listing_data.copy()
        updated_data["compensation"] = 150.0
        mock_listing_crud.update_listing = AsyncMock(return_value=updated_data)
        
        payload = {"compensation": 150.0}
        
        response = listings_client.patch(
            f"/api/v1/listings/{test_listing_id}?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["compensation"] == 150.0

    @pytest.mark.asyncio
    async def test_update_listing_not_found(
        self, listings_client, mock_listing_crud, test_listing_id, test_poster_uid
    ):
        """Test updating non-existent listing."""
        mock_listing_crud.update_listing = AsyncMock(return_value=None)
        
        payload = {"name": "Updated Listing"}
        
        response = listings_client.patch(
            f"/api/v1/listings/{test_listing_id}?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== DELETE LISTING TESTS ====================

class TestDeleteListing:
    """Tests for DELETE /listings/{listing_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_listing_success(
        self, listings_client, mock_listing_crud, test_listing_id, test_poster_uid
    ):
        """Test successfully deleting a listing."""
        mock_listing_crud.delete_listing = AsyncMock(return_value=True)
        
        response = listings_client.delete(
            f"/api/v1/listings/{test_listing_id}?user_uid={test_poster_uid}"
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_listing_crud.delete_listing.assert_called_once_with(test_listing_id, test_poster_uid)

    @pytest.mark.asyncio
    async def test_delete_listing_not_found(
        self, listings_client, mock_listing_crud, test_listing_id, test_poster_uid
    ):
        """Test deleting non-existent listing."""
        mock_listing_crud.delete_listing = AsyncMock(return_value=False)
        
        response = listings_client.delete(
            f"/api/v1/listings/{test_listing_id}?user_uid={test_poster_uid}"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== APPLY TO LISTING TESTS ====================

class TestApplyToListing:
    """Tests for POST /listings/{listing_id}/apply endpoint."""

    @pytest.mark.asyncio
    async def test_apply_to_listing_success(
        self, listings_client, mock_listing_crud, test_listing_id, test_applicant_uid, test_applicant_data
    ):
        """Test successfully applying to a listing."""
        mock_listing_crud.apply_to_listing = AsyncMock(return_value=test_applicant_data)
        
        payload = {"message": "I'm interested in this listing"}
        
        response = listings_client.post(
            f"/api/v1/listings/{test_listing_id}/apply?user_uid={test_applicant_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["listing_id"] == str(test_listing_id)
        assert data["applicant_uid"] == str(test_applicant_uid)
        assert data["status"] == "applied"
        mock_listing_crud.apply_to_listing.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_to_listing_without_message(
        self, listings_client, mock_listing_crud, test_listing_id, test_applicant_uid, test_applicant_data
    ):
        """Test applying without optional message."""
        mock_listing_crud.apply_to_listing = AsyncMock(return_value=test_applicant_data)
        
        payload = {}
        
        response = listings_client.post(
            f"/api/v1/listings/{test_listing_id}/apply?user_uid={test_applicant_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_apply_to_listing_failure(
        self, listings_client, mock_listing_crud, test_listing_id, test_applicant_uid
    ):
        """Test failed application (already applied or listing not open)."""
        mock_listing_crud.apply_to_listing = AsyncMock(return_value=None)
        
        payload = {"message": "I'm interested"}
        
        response = listings_client.post(
            f"/api/v1/listings/{test_listing_id}/apply?user_uid={test_applicant_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== GET LISTING APPLICANTS TESTS ====================

class TestGetListingApplicants:
    """Tests for GET /listings/{listing_id}/applicants endpoint."""

    @pytest.mark.asyncio
    async def test_get_listing_applicants_success(
        self, listings_client, mock_listing_crud, test_listing_id
    ):
        """Test successfully getting listing applicants."""
        applicants = [
            {"listing_id": test_listing_id, "applicant_uid": uuid4(), "status": "applied", "applied_at": datetime.utcnow().isoformat()},
            {"listing_id": test_listing_id, "applicant_uid": uuid4(), "status": "shortlisted", "applied_at": datetime.utcnow().isoformat()},
        ]
        mock_listing_crud.get_listing_applicants = AsyncMock(return_value=applicants)
        
        response = listings_client.get(f"/api/v1/listings/{test_listing_id}/applicants")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_listing_crud.get_listing_applicants.assert_called_once_with(test_listing_id)

    @pytest.mark.asyncio
    async def test_get_listing_applicants_empty(
        self, listings_client, mock_listing_crud, test_listing_id
    ):
        """Test getting applicants for listing with no applications."""
        mock_listing_crud.get_listing_applicants = AsyncMock(return_value=[])
        
        response = listings_client.get(f"/api/v1/listings/{test_listing_id}/applicants")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


# ==================== UPDATE APPLICANT STATUS TESTS ====================

class TestUpdateApplicantStatus:
    """Tests for PATCH /listings/{listing_id}/applicants/{applicant_uid} endpoint."""

    @pytest.mark.asyncio
    async def test_update_applicant_status_success(
        self, listings_client, mock_listing_crud, test_listing_id, test_applicant_uid, test_poster_uid, test_applicant_data
    ):
        """Test successfully updating applicant status."""
        updated_data = test_applicant_data.copy()
        updated_data["status"] = "shortlisted"
        mock_listing_crud.update_applicant_status = AsyncMock(return_value=updated_data)
        
        payload = {"status": "shortlisted"}
        
        response = listings_client.patch(
            f"/api/v1/listings/{test_listing_id}/applicants/{test_applicant_uid}?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "shortlisted"
        mock_listing_crud.update_applicant_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_applicant_status_to_rejected(
        self, listings_client, mock_listing_crud, test_listing_id, test_applicant_uid, test_poster_uid, test_applicant_data
    ):
        """Test updating applicant status to rejected."""
        updated_data = test_applicant_data.copy()
        updated_data["status"] = "rejected"
        mock_listing_crud.update_applicant_status = AsyncMock(return_value=updated_data)
        
        payload = {"status": "rejected"}
        
        response = listings_client.patch(
            f"/api/v1/listings/{test_listing_id}/applicants/{test_applicant_uid}?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_update_applicant_status_not_found(
        self, listings_client, mock_listing_crud, test_listing_id, test_applicant_uid, test_poster_uid
    ):
        """Test updating non-existent application."""
        mock_listing_crud.update_applicant_status = AsyncMock(return_value=None)
        
        payload = {"status": "shortlisted"}
        
        response = listings_client.patch(
            f"/api/v1/listings/{test_listing_id}/applicants/{test_applicant_uid}?user_uid={test_poster_uid}",
            json=payload
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== GET USER APPLICATIONS TESTS ====================

class TestGetUserApplications:
    """Tests for GET /listings/users/{user_uid}/applications endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_applications_success(
        self, listings_client, mock_listing_crud, test_applicant_uid
    ):
        """Test successfully getting user's applications."""
        applications = [
            {"listing_id": uuid4(), "applicant_uid": test_applicant_uid, "status": "applied", "applied_at": datetime.utcnow().isoformat()},
            {"listing_id": uuid4(), "applicant_uid": test_applicant_uid, "status": "shortlisted", "applied_at": datetime.utcnow().isoformat()},
            {"listing_id": uuid4(), "applicant_uid": test_applicant_uid, "status": "rejected", "applied_at": datetime.utcnow().isoformat()},
        ]
        mock_listing_crud.get_user_applications = AsyncMock(return_value=applications)
        
        response = listings_client.get(f"/api/v1/listings/users/{test_applicant_uid}/applications")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        mock_listing_crud.get_user_applications.assert_called_once_with(test_applicant_uid)

    @pytest.mark.asyncio
    async def test_get_user_applications_empty(
        self, listings_client, mock_listing_crud, test_applicant_uid
    ):
        """Test getting applications for user with no applications."""
        mock_listing_crud.get_user_applications = AsyncMock(return_value=[])
        
        response = listings_client.get(f"/api/v1/listings/users/{test_applicant_uid}/applications")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
