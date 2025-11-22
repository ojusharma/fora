"""
API endpoints for tag operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.core.database import get_supabase_client
from app.crud.tag import TagCRUD
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCY ====================

def get_tag_crud(supabase: Client = Depends(get_supabase_client)) -> TagCRUD:
    """Dependency to get TagCRUD instance."""
    return TagCRUD(supabase)


# ==================== TAG ENDPOINTS ====================

@router.post(
    "/",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
)
async def create_tag(
    tag: TagCreate,
    crud: TagCRUD = Depends(get_tag_crud),
):
    """
    Create a new tag.
    
    - **name**: Tag name (must be unique)
    """
    try:
        result = await crud.create_tag(tag)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create tag",
            )
        return result
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{tag.name}' already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tag: {str(e)}",
        )


@router.get(
    "/",
    response_model=List[TagResponse],
    summary="Get all tags",
)
async def get_tags(
    search: Optional[str] = Query(None, description="Search tags by name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tags to return"),
    offset: int = Query(0, ge=0, description="Number of tags to skip"),
    crud: TagCRUD = Depends(get_tag_crud),
):
    """
    Get all tags with optional search filter.
    
    - **search**: Optional search term to filter tags by name (case-insensitive)
    - **limit**: Maximum number of tags to return (default: 100)
    - **offset**: Number of tags to skip for pagination (default: 0)
    """
    tags = await crud.get_all_tags(limit=limit, offset=offset, search=search)
    return tags


@router.get(
    "/count",
    response_model=dict,
    summary="Get total count of tags",
)
async def get_tags_count(
    search: Optional[str] = Query(None, description="Search tags by name"),
    crud: TagCRUD = Depends(get_tag_crud),
):
    """
    Get total count of tags.
    
    - **search**: Optional search term to filter tags by name (case-insensitive)
    """
    count = await crud.get_tags_count(search=search)
    return {"count": count}


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Get a tag by ID",
)
async def get_tag(
    tag_id: int,
    crud: TagCRUD = Depends(get_tag_crud),
):
    """
    Get a specific tag by ID.
    
    - **tag_id**: Tag ID
    """
    tag = await crud.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found",
        )
    return tag


@router.get(
    "/name/{tag_name}",
    response_model=TagResponse,
    summary="Get a tag by name",
)
async def get_tag_by_name(
    tag_name: str,
    crud: TagCRUD = Depends(get_tag_crud),
):
    """
    Get a specific tag by name.
    
    - **tag_name**: Tag name
    """
    tag = await crud.get_tag_by_name(tag_name)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with name '{tag_name}' not found",
        )
    return tag


@router.put(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Update a tag",
)
async def update_tag(
    tag_id: int,
    tag: TagUpdate,
    crud: TagCRUD = Depends(get_tag_crud),
):
    """
    Update a tag.
    
    - **tag_id**: Tag ID
    - **name**: New tag name
    """
    try:
        result = await crud.update_tag(tag_id, tag)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found",
            )
        return result
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{tag.name}' already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update tag: {str(e)}",
        )


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag",
)
async def delete_tag(
    tag_id: int,
    crud: TagCRUD = Depends(get_tag_crud),
):
    """
    Delete a tag.
    
    - **tag_id**: Tag ID
    
    Note: This will fail if the tag is still referenced in listing_tags or user_preferences
    due to foreign key constraints.
    """
    success = await crud.delete_tag(tag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found",
        )
    return None
