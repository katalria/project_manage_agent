from fastapi import APIRouter, HTTPException
from datetime import datetime
from uuid import uuid4
import os

from utils.logger import get_logger
from story.services import StoryGeneratorAgent
from story.models import StoryRequest, StoryResponse

router = APIRouter(prefix="/Story", tags=["Story"])

logger = get_logger(__name__)

# EpicGeneratorService 인스턴스 생성
story_service = StoryGeneratorAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@router.post("/generate-storys", response_model=StoryResponse)
def generate_storys(request: StoryRequest):
    """스토리 동기 생성"""
    try:
        start_time = datetime.now()
        
        storys = story_service.generate_storys(request)
        
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
