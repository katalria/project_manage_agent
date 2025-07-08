from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os
from src.services.project_management_orchestrator import ProjectManagementOrchestrator
from src.models.models import TaskListInput


router = APIRouter()

# 전역 orchestrator 인스턴스
orchestrator = ProjectManagementOrchestrator()


class TaskProcessRequest(BaseModel):
    tasks: List[str]
    estimate_points: bool = True
    reference_csv_path: Optional[str] = None


class StoryEstimationRequest(BaseModel):
    epic_story_data: dict
    

@router.post("/process-tasks", 
             summary="태스크 분류 및 포인트 추정",
             description="입력된 Task 리스트를 Epic/Story로 분류하고 스토리 포인트를 추정합니다.")
async def process_tasks(request: TaskProcessRequest):
    """
    태스크들을 Epic/Story로 분류하고 스토리 포인트를 추정합니다.
    """
    try:
        # 참고 CSV 파일이 지정된 경우 로드
        if request.reference_csv_path:
            success = orchestrator.load_reference_data(request.reference_csv_path)
            if not success:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to load reference CSV: {request.reference_csv_path}"
                )
        
        # 태스크 처리
        result = orchestrator.process_tasks_with_estimation(
            tasks=request.tasks,
            estimate_points=request.estimate_points
        )
        
        # 요약 정보 추가
        if request.estimate_points:
            summary = orchestrator.get_estimation_summary(result)
            result["summary"] = summary
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/upload-reference", 
             summary="참고 스토리 CSV 업로드",
             description="스토리 포인트 추정을 위한 참고 데이터 CSV 파일을 업로드합니다.")
async def upload_reference_csv(file: UploadFile = File(...)):
    """
    참고 스토리 데이터 CSV 파일을 업로드하고 로드합니다.
    CSV 파일은 title, description, point, area 컬럼을 포함해야 합니다.
    """
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # CSV 로드 시도
        success = orchestrator.load_reference_data(tmp_file_path)
        
        # 임시 파일 삭제
        os.unlink(tmp_file_path)
        
        if success:
            return {"message": "Reference CSV loaded successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to load CSV file")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/estimate-stories",
             summary="기존 스토리 포인트 추정", 
             description="이미 분류된 Epic/Story 데이터에 대해 스토리 포인트를 추정합니다.")
async def estimate_story_points(request: StoryEstimationRequest):
    """
    기존 Epic/Story 데이터에 대해 스토리 포인트만 추정합니다.
    """
    try:
        result = orchestrator.estimate_existing_stories(request.epic_story_data)
        summary = orchestrator.get_estimation_summary(result)
        result["summary"] = summary
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Estimation failed: {str(e)}")


@router.post("/classify-only",
             summary="태스크 분류만 수행",
             description="스토리 포인트 추정 없이 태스크를 Epic/Story로만 분류합니다.")
async def classify_tasks_only(task_list: TaskListInput):
    """
    스토리 포인트 추정 없이 태스크를 Epic/Story로만 분류합니다.
    """
    try:
        result = orchestrator.process_tasks_with_estimation(
            tasks=task_list.tasks,
            estimate_points=False
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.get("/health",
            summary="헬스 체크",
            description="서비스 상태를 확인합니다.")
async def health_check():
    """
    서비스 상태를 확인합니다.
    """
    return {
        "status": "healthy",
        "epic_agent": "ready",
        "story_point_agent": "ready",
        "reference_data_loaded": orchestrator.point_agent.reference_data is not None
    }