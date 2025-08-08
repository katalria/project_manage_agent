from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from uuid import uuid4
import os

from utils.logger import get_logger
from epic.services import EpicGeneratorAgent
from epic.models import EpicRequest, EpicResponse

router = APIRouter(prefix="/epic", tags=["Epic"])

logger = get_logger(__name__)

# EpicGeneratorService 인스턴스 생성
epic_service = EpicGeneratorAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@router.post("/generate-epics", response_model=EpicResponse)
def generate_epics(request: EpicRequest):
    """에픽 동기 생성"""
    try:
        start_time = datetime.now()
        
        epics = epic_service.generate_epics(request)
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        return EpicResponse(
            epics=epics,
            total_count=len(epics),
            generation_time=generation_time
        )
        
    except Exception as e:
        logger.error(f"에픽 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert-task-to-epics", response_model=EpicResponse)
def convert_task_to_epics(request: EpicRequest):
    """동기 업무 - 에픽 변환 생성"""
    try:
        start_time = datetime.now()
        
        epics = epic_service.convert_tasks_to_epics(request)
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        return EpicResponse(
            epics=epics,
            total_count=len(epics),
            generation_time=generation_time
        )
        
    except Exception as e:
        logger.error(f"동기 업무 - 에픽 변환 생성: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
