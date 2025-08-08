from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from story.models import Story
from epic.models import Epic


class StoryPointEstimation(BaseModel):
    """스토리 포인트 추정 결과 모델"""
    story_title: str = Field(..., description="스토리 제목")
    estimated_point: int = Field(..., ge=1, le=8, description="추정된 스토리 포인트 (1,2,3,5,8)")
    domain: str = Field(..., description="스토리 영역 (frontend|backend|devops|data)")
    estimation_method: str = Field(..., description="추정 방법 (same_area|cross_area)")
    reasoning: str = Field(..., description="상세한 추정 근거 (왜 이 포인트인지 논리적 설명)")
    complexity_factors: List[str] = Field(default_factory=list, description="복잡도 요소들")
    similar_stories: List[str] = Field(default_factory=list, description="유사한 참고 스토리 제목들 (영역 구분 없이)")
    confidence_level: str = Field(..., description="신뢰도 수준 (high|medium|low)")
    assumptions: List[str] = Field(default_factory=list, description="추정 시 가정한 사항들")
    risks: List[str] = Field(default_factory=list, description="예상되는 위험 요소들")


class StoryPointRequest(BaseModel):
    """스토리 포인트 추정 요청 모델"""
    user_input: str = Field(..., description="사용자 입력")
    epic_info: Optional[Epic] = Field(None, description="에픽 정보")
    story_info: Story = Field(..., description="스토리 정보")
    reference_stories: List[Dict[str, Any]] = Field(default_factory=list, description="참고 스토리들")


class StoryPointResponse(BaseModel):
    """스토리 포인트 추정 응답 모델"""
    estimations: List[StoryPointEstimation]
    total_count: int
    generation_time: float


