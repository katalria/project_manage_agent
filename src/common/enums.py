from enum import Enum


class AgentType(str, Enum):
    EPIC = "epic"
    STORY = "story"
    POINT = "point"
    TASK = "task"
    SCHEDULE = "schedule"


class WorkflowStep(str, Enum):
    EPIC_GENERATION = "epic_generation"
    STORY_GENERATION = "story_generation"
    POINT_ESTIMATION = "point_estimation"
    TASK_BREAKDOWN = "task_breakdown"
    SCHEDULE_PLANNING = "schedule_planning"


class FeedbackAction(str, Enum):
    APPROVE = "approve"
    MODIFY = "modify"
    REJECT = "reject"
    SKIP = "skip"

class WorkflowStatus(str, Enum):
    """워크플로우 상태"""
    ACTIVE = "active"          # 진행 중
    PAUSED = "paused"          # 일시 중지
    COMPLETED = "completed"    # 완료
    FAILED = "failed"          # 실패
    CANCELLED = "cancelled"    # 취소