from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Task(BaseModel):
    """태스크 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    story_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    estimated_hours: Optional[float] = Field(None, ge=0, description="예상 시간")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)