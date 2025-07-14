from pydantic import BaseModel, Field
from typing import List

class ProjectInfo(BaseModel):
    """
    프로젝트 정보 저장 모델
    """
    name: str = Field(..., description="프로젝트 이름")
    description: str = Field(..., description="프로젝트 설명")
    goals: List[str] = Field(..., description="프로젝트 목표들")
    requirements: List[str] = Field(..., description="프로젝트 요구사항들")
    constraints: List[str] = Field(default_factory=list, description="제약사항")