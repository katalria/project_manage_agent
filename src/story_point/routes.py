from fastapi import APIRouter, HTTPException
from datetime import datetime
import os

from utils.logger import get_logger
from story_point.services import StoryPointEstimationAgent
from story_point.models import StoryPointRequest, StoryPointResponse

router = APIRouter(prefix="/story-point", tags=["StoryPoint"])

logger = get_logger(__name__)

# StoryPointEstimationAgent 인스턴스 생성
story_point_service = StoryPointEstimationAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@router.post("/estimate", response_model=StoryPointResponse)
def estimate_story_points(request: StoryPointRequest):
    """스토리 포인트 동기 추정"""
    try:
        start_time = datetime.now()
        
        estimations = story_point_service.estimate_story_points(request)
        
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


@router.get("/reference-data/reload")
def reload_reference_data():
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
def get_reference_data_stats():
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

