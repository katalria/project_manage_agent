from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from uuid import uuid4
import os

from utils.logger import get_logger
from epic.services import EpicGeneratorAgent
from epic.models import EpicRequest, EpicResponse, ProcessingStatus

router = APIRouter(prefix="/epic", tags=["Epic"])

logger = get_logger(__name__)

# EpicGeneratorService 인스턴스 생성
epic_service = EpicGeneratorAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@router.post("/generate-epics", response_model=EpicResponse)
async def generate_epics(request: EpicRequest):
    """에픽 동기 생성"""
    try:
        start_time = datetime.now()
        
        epics = await epic_service.generate_epics(request)
        
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

@router.post("/generate-epics-async")
async def generate_epics_async(request: EpicRequest, background_tasks: BackgroundTasks):
    """에픽 비동기 생성"""
    try:
        task_id = str(uuid4())
        
        # 초기 상태 설정
        epic_service.processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="pending",
            message="에픽 생성 대기 중..."
        )
        
        # 백그라운드 태스크 추가
        background_tasks.add_task(
            epic_service.generate_epics_async, 
            request, 
            task_id
        )
        
        return {"task_id": task_id, "message": "에픽 생성 작업이 시작되었습니다."}
        
    except Exception as e:
        logger.error(f"비동기 에픽 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/convert-task-to-epics", response_model=EpicResponse)
async def convert_task_to_epics(request: EpicRequest):
    """동기 업무 - 에픽 변환 생성"""
    try:
        start_time = datetime.now()
        
        epics = await epic_service.convert_tasks_to_epics(request)
        
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

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    status = epic_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    return status

@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now()}