from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from uuid import uuid4
import os

from utils.logger import get_logger
from story.services import StoryGeneratorAgent
from story.models import StoryRequest, StoryResponse, ProcessingStatus

router = APIRouter(prefix="/Story", tags=["Story"])

logger = get_logger(__name__)

# EpicGeneratorService 인스턴스 생성
story_service = StoryGeneratorAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@router.post("/generate-storys", response_model=StoryResponse)
async def generate_storys(request: StoryRequest):
    """스토리 동기 생성"""
    try:
        start_time = datetime.now()
        
        storys = await story_service.generate_storys(request)
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        return StoryResponse(
            storys=storys,
            total_count=len(storys),
            generation_time=generation_time
        )
        
    except Exception as e:
        logger.error(f"스토리 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-storys-async")
async def generate_storys_async(request: StoryRequest, background_tasks: BackgroundTasks):
    """스토리 비동기 생성"""
    try:
        task_id = str(uuid4())
        
        # 초기 상태 설정
        story_service.processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="pending",
            message="스토리 생성 대기 중..."
        )
        
        # 백그라운드 태스크 추가
        background_tasks.add_task(
            story_service.generate_storys, 
            request, 
            task_id
        )
        
        return {"task_id": task_id, "message": "스토리 생성 작업이 시작되었습니다."}
        
    except Exception as e:
        logger.error(f"비동기 스토리 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    status = story_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    return status

@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now()}