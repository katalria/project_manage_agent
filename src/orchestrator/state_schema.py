# orchestrator/state_schema.py
from typing import TypedDict, Literal, List, Optional, Dict
from datetime import datetime

from epic.models import Epic
from story.models import Story
from story_point.models import StoryPointEstimation


class OrchestratorState(TypedDict, total=False):
    """통합 오케스트레이터 상태 스키마"""
    
    # 입력 데이터
    user_input: str
    project_info: Optional[str]
    
    # 분석 결과 (QueryAnalyzer에서 결정)
    workflow_type: Literal["epic_only", "story_only", "point_only", "full_pipeline"]
    required_steps: List[str]
    
    # 각 단계 결과
    epics: Optional[List[Epic]]
    stories: Optional[List[Story]]
    story_points: Optional[List[StoryPointEstimation]]
    
    # 실행 상태
    current_step: str
    completed_steps: List[str]
    errors: List[str]
    
    # 메타데이터
    execution_start_time: Optional[datetime]
    step_times: Dict[str, float]
    
    # 라우팅 제어
    next_action: Literal["analyze", "epic", "story", "point", "done"]


# 기존 호환성을 위한 별칭
AgentState = OrchestratorState
