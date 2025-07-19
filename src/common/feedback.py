from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .enums import WorkflowStep, FeedbackAction
from epic.models import Epic
from story.models import Story
from task.models import Task

class EpicFeedback(BaseModel):
    """에픽 피드백"""
    session_id: str
    epic_modifications: List[Epic] = Field(default_factory=list)
    new_epics: List[Epic] = Field(default_factory=list)
    removed_epic_ids: List[str] = Field(default_factory=list)
    comments: Optional[str] = None

class StoryFeedback(BaseModel):
    """스토리 피드백"""
    session_id: str
    story_modifications: List[Story] = Field(default_factory=list)
    new_stories: List[Story] = Field(default_factory=list)
    removed_story_ids: List[str] = Field(default_factory=list)
    comments: Optional[str] = None

class PointFeedback(BaseModel):
    """포인트 추정 피드백"""
    session_id: str
    point_adjustments: Dict[str, int] = Field(default_factory=dict)  # story_id -> new_points
    reasoning: Optional[Dict[str, str]] = Field(default_factory=dict)  # story_id -> reason
    comments: Optional[str] = None

class TaskFeedback(BaseModel):
    """태스크 피드백"""
    session_id: str
    task_modifications: List[Task] = Field(default_factory=list)
    new_tasks: List[Task] = Field(default_factory=list)
    removed_task_ids: List[str] = Field(default_factory=list)
    comments: Optional[str] = None

class ScheduleFeedback(BaseModel):
    """일정 피드백"""
    session_id: str
    deadline_adjustment: Optional[datetime] = None
    milestone_changes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    comments: Optional[str] = None

class FeedbackRequest(BaseModel):
    """통합 피드백 요청"""
    session_id: str
    step: WorkflowStep
    action: FeedbackAction
    feedback_data: Union[EpicFeedback, StoryFeedback, PointFeedback, TaskFeedback, ScheduleFeedback]
    comments: Optional[str] = None