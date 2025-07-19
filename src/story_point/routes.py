from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from uuid import uuid4
import os

from utils.logger import get_logger
from story_point.services import StoryPointEstimationAgent
from story_point.models import StoryPointRequest, StoryPointResponse, StoryPointProcessingStatus

router = APIRouter(prefix="/story-point", tags=["StoryPoint"])

logger = get_logger(__name__)

# StoryPointEstimationAgent 인스턴스 생성
story_point_service = StoryPointEstimationAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@router.post("/estimate", response_model=StoryPointResponse)
async def estimate_story_points(request: StoryPointRequest):
    """스토리 포인트 동기 추정"""
    try:
        start_time = datetime.now()
        
        estimations = await story_point_service.estimate_story_points(request)
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        return StoryPointResponse(
            estimations=estimations,
            total_count=len(estimations),
            generation_time=generation_time
        )
        
    except Exception as e:
        logger.error(f"스토리 포인트 추정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate-async")
async def estimate_story_points_async(request: StoryPointRequest, background_tasks: BackgroundTasks):
    """스토리 포인트 비동기 추정"""
    try:
        task_id = str(uuid4())
        
        # 초기 상태 설정
        story_point_service.processing_tasks[task_id] = StoryPointProcessingStatus(
            task_id=task_id,
            status="pending",
            message="스토리 포인트 추정 대기 중..."
        )
        
        # 백그라운드 태스크 추가
        background_tasks.add_task(
            story_point_service.estimate_story_points_async, 
            request, 
            task_id
        )
        
        return {"task_id": task_id, "message": "스토리 포인트 추정 작업이 시작되었습니다."}
        
    except Exception as e:
        logger.error(f"비동기 스토리 포인트 추정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    status = story_point_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    return status


@router.get("/reference-data/reload")
async def reload_reference_data():
    """참고 데이터 다시 로드"""
    try:
        success = story_point_service.load_reference_data()
        if success:
            return {"message": "참고 데이터가 성공적으로 다시 로드되었습니다.", "status": "success"}
        else:
            return {"message": "참고 데이터 로드에 실패했습니다.", "status": "failed"}
    except Exception as e:
        logger.error(f"참고 데이터 로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reference-data/stats")
async def get_reference_data_stats():
    """참고 데이터 통계"""
    try:
        if story_point_service.reference_data is None or story_point_service.reference_data.empty:
            return {"total_stories": 0, "domains": []}
        
        total_stories = len(story_point_service.reference_data)
        domains = story_point_service.reference_data['domain'].value_counts().to_dict()
        
        return {
            "total_stories": total_stories,
            "domains": domains,
            "csv_file_path": story_point_service.csv_file_path
        }
    except Exception as e:
        logger.error(f"참고 데이터 통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now()}