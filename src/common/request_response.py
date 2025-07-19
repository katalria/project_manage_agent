from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .enums import AgentType, WorkflowStep
from epic.models import Epic
from story.models import Story
from task.models import Task

class ProjectInfo(BaseModel):
    """프로젝트 정보"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    requirements: List[str] = Field(..., min_items=1)

class AgentRequest(BaseModel):
    """Agent 실행 요청"""
    input_data: Dict[str, Any] = Field(..., description="Agent 입력 데이터")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 컨텍스트")
    session_id: Optional[str] = Field(None, description="워크플로우 세션 ID")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Agent 옵션")

class AgentResponse(BaseModel):
    """Agent 실행 응답"""
    agent_type: AgentType
    result: Union[List[Epic], List[Story], List[Task], Dict[str, Any]]
    session_id: str
    step: WorkflowStep
    timestamp: datetime = Field(default_factory=datetime.now)
    requires_feedback: bool = True
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    execution_time_ms: Optional[int] = Field(None, ge=0)