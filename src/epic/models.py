from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class Epic(BaseModel):
    """에픽 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    business_value: str = Field(..., description="에픽 비즈니스 가치")
    priority: str = Field(..., description="에픽 중요도")
    acceptance_criteria: List[str] = Field(default_factory=list)
    included_tasks: Optional[List[str]] = Field(..., description="포함된 업무 리스트")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EpicRequest(BaseModel):
    """에픽 생성 요청 모델"""
    user_input: str = Field(..., description="사용자 입력")
    project_info: str = Field(..., description="프로젝트 정보")
    max_epics: int = Field(default=5, description="최대 에픽 개수")


class EpicResponse(BaseModel):
    """에픽 생성 응답 모델"""
    epics: List[Epic]
    total_count: int
    generation_time: float


