from pydantic import BaseModel, Field
from typing import List

class TaskInput(BaseModel):
    task: str = Field(..., description="업무 내용")


class TaskListInput(BaseModel):
    tasks: List[str] = Field(..., description="업무 목록")


class Story(BaseModel):
    title: str = Field(..., description="스토리 제목")
    description: str = Field(..., description="스토리 설명")
    acceptance_criteria: List[str] = Field(..., description="완료조건")
    point: int = Field(..., ge=1, le=8, description="스토리 포인트 (1-8)")
    area: str = Field(..., description="담당 영역")
    dependencies : List[str] = Field(..., description="의존성 있는 다른 Story ID")


class Epic(BaseModel):
    title: str = Field(..., description="에픽 제목")
    description: str = Field(..., description="에픽 설명")
    business_value: str = Field(..., description="에픽 비즈니스 가치")
    priority: str = Field(..., description="에픽 중요도")


class EpicStoryGroup(BaseModel):
    epic: Epic
    stories: List[Story]


class TaskClassificationResponse(BaseModel):
    result: List[EpicStoryGroup] = Field(..., description="에픽과 스토리로 분류된 결과")