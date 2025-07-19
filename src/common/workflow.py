from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .enums import WorkflowStep, WorkflowStatus
from .request_response import ProjectInfo, AgentResponse


class WorkflowConfig(BaseModel):
    """워크플로우 설정"""
    steps: List[WorkflowStep] = Field(..., min_items=1)
    auto_continue: bool = Field(False, description="자동 진행 여부")
    project_info: ProjectInfo
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('steps')
    @classmethod
    def validate_steps_order(cls, v):
        valid_order = list(WorkflowStep)
        for i, step in enumerate(v):
            if i > 0 and valid_order.index(step) <= valid_order.index(v[i-1]):
                raise ValueError('워크플로우 단계는 올바른 순서여야 합니다')
        return v

class WorkflowSession(BaseModel):
    """워크플로우 세션"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: WorkflowConfig
    current_step: WorkflowStep
    completed_steps: List[WorkflowStep] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error_log: List[str] = Field(default_factory=list)

# ==================== 응답 모델 ====================

class WorkflowStartResponse(BaseModel):
    """워크플로우 시작 응답"""
    session_id: str
    current_step: WorkflowStep
    result: AgentResponse
    next_action: str = "await_feedback"

class WorkflowContinueResponse(BaseModel):
    """워크플로우 계속 응답"""
    session_id: str
    current_step: WorkflowStep
    result: Optional[AgentResponse] = None
    next_action: str
    completed: bool = False

class WorkflowStatusResponse(BaseModel):
    """워크플로우 상태 응답"""
    session: WorkflowSession
    progress_percentage: float = Field(ge=0, le=100)
    estimated_completion: Optional[datetime] = None

class ErrorResponse(BaseModel):
    """에러 응답"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)