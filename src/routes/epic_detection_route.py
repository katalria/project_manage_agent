from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from src.services.epic_detection_agent import EpicDetectionAgent

router = APIRouter()
agent = EpicDetectionAgent()

class TaskList(BaseModel):
    tasks: List[str]

@router.post("/", summary="에픽 자동 추출", description="입력된 Task 리스트를 기반으로 Epic 및 Story를 자동 분류합니다.")
async def generate_epics(task_list: TaskList):
    result = agent.extract_epics(task_list.tasks)
    return result
