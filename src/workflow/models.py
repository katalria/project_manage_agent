from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, TypedDict
from datetime import datetime

from epic.models import Epic, EpicRequest
from story.models import Story, StoryRequest
from story_point.models import StoryPointEstimation, StoryPointRequest


class WorkflowRequest(BaseModel):
    """워크플로우 요청 모델"""
    user_input: str = Field(..., description="사용자 입력")
    project_info: str = Field(default="", description="프로젝트 정보")
    max_epics: int = Field(default=3, description="최대 에픽 개수")
    max_stories_per_epic: int = Field(default=5, description="에픽당 최대 스토리 개수")


class EpicWithStoriesAndEstimations(BaseModel):
    """에픽과 관련 스토리 및 추정 결과"""
    epic: Epic
    stories: List[Story]
    story_point_estimations: List[StoryPointEstimation]
    
    
class WorkflowResponse(BaseModel):
    """워크플로우 응답 모델"""
    epic_results: List[EpicWithStoriesAndEstimations]
    total_epics: int
    total_stories: int
    total_estimations: int
    execution_time: float
    workflow_status: str


class WorkflowProcessingStatus(BaseModel):
    """워크플로우 처리 상태 모델"""
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    current_step: str
    message: str
    progress: int  # 0-100
    result: Optional[WorkflowResponse] = None
    error: Optional[str] = None


class ProjectManagementState(TypedDict):
    """프로젝트 관리 워크플로우 상태"""
    # 입력 데이터
    user_input: str
    project_info: str
    max_epics: int
    max_stories_per_epic: int
    
    # 처리 과정 데이터
    epic_request: Optional[EpicRequest]
    generated_epics: List[Epic]
    
    story_requests: List[StoryRequest]
    generated_stories: List[Story]
    
    story_point_requests: List[StoryPointRequest]
    story_point_estimations: List[StoryPointEstimation]
    
    # 메타데이터
    current_step: str
    errors: List[str]
    execution_start_time: Optional[datetime]
    step_times: Dict[str, float]