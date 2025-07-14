from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, TypedDict
from datetime import datetime
import uuid

from epic.models import Epic
from project.models import P


class Story(BaseModel):
    """스토리 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    epic_id: Optional[str] = Field(None, exclude=True, description= "epic generator 결과 epic id")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    acceptance_criteria: List[str] = Field(default_factory=list)
    story_points: Optional[int] = Field(None, ge=0, description="스토리 포인트")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StoryRequest(BaseModel):
    """스토리 생성 요청 모델"""
    user_input: str = Field(..., description="사용자 입력")
    epic_info: Optional[Epic] = Field(None, exclude=True, description= "epic generator 결과 epic 정보")
    max_storys: int = Field(default=5, description="최대 스토리 개수")


class StoryResponse(BaseModel):
    """스토리 생성 응답 모델"""
    storys: List[Story]
    total_count: int
    generation_time: float


class ProcessingStatus(BaseModel):
    """처리 상태 모델"""
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    message: str
    result: Optional[List[Epic]] = None
    error: Optional[str] = None


class StoryGenerationState(TypedDict):
    """LangGraph State"""
    user_input: str
    epic_info: str
    max_storys: int
    raw_response: str
    parsed_epics: List[Dict[str, Any]]
    validated_epics: List[Epic]
    errors: List[str]
    current_step: str    