from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.content import Content, ContentChange, ContentType

router = APIRouter()


class ContentItem(BaseModel):
    id: UUID
    competitor_id: UUID
    url: str
    title: str
    content_type: ContentType
    word_count: int
    readability_score: Optional[float]
    has_changed: bool
    last_modified: Optional[datetime]
    last_checked: datetime
    
    class Config:
        from_attributes = True


class ContentChangeItem(BaseModel):
    id: UUID
    content_id: UUID
    change_type: str
    field_changed: str
    old_value: Optional[str]
    new_value: Optional[str]
    detected_at: datetime
    
    class Config:
        from_attributes = True


class ContentDiff(BaseModel):
    content_id: UUID
    url: str
    title: str
    diff_html: Optional[str]
    old_content: Optional[str]
    new_content: Optional[str]
    detected_at: datetime


@router.get("/{competitor_id}", response_model=List[ContentItem])
async def get_competitor_content(
    competitor_id: UUID,
    content_type: Optional[ContentType] = None,
    has_changed: Optional[bool] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all tracked content for a competitor."""
    
    query = select(Content).where(Content.competitor_id == competitor_id)
    
    if content_type:
        query = query.where(Content.content_type == content_type)
    
    if has_changed is not None:
        query = query.where(Content.has_changed == has_changed)
    
    query = query.order_by(Content.last_checked.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{competitor_id}/changes", response_model=List[ContentChangeItem])
async def get_content_changes(
    competitor_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get recent content changes for a competitor."""
    
    result = await db.execute(
        select(ContentChange)
        .join(Content)
        .where(Content.competitor_id == competitor_id)
        .order_by(ContentChange.detected_at.desc())
        .limit(limit)
    )
    
    return result.scalars().all()


@router.get("/diff/{content_id}", response_model=ContentDiff)
async def get_content_diff(
    content_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get diff view for a specific content change."""
    
    # Get content
    content_result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = content_result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Get latest change
    change_result = await db.execute(
        select(ContentChange)
        .where(ContentChange.content_id == content_id)
        .order_by(ContentChange.detected_at.desc())
        .limit(1)
    )
    change = change_result.scalar_one_or_none()
    
    return ContentDiff(
        content_id=content.id,
        url=content.url,
        title=content.title,
        diff_html=change.diff_html if change else None,
        old_content=change.old_value if change else None,
        new_content=change.new_value if change else None,
        detected_at=change.detected_at if change else content.last_checked
    )


@router.get("/stats/{competitor_id}")
async def get_content_stats(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get content statistics for a competitor."""
    
    result = await db.execute(
        select(Content).where(Content.competitor_id == competitor_id)
    )
    contents = result.scalars().all()
    
    type_counts = {}
    total_words = 0
    changed_count = 0
    
    for content in contents:
        type_name = content.content_type.value
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
        total_words += content.word_count
        if content.has_changed:
            changed_count += 1
    
    return {
        "total_pages": len(contents),
        "total_words": total_words,
        "average_words": total_words // len(contents) if contents else 0,
        "changed_pages": changed_count,
        "content_types": type_counts
    }
