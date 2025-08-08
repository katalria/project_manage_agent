from fastapi import APIRouter, HTTPException
from datetime import datetime
from uuid import uuid4
import os

from utils.logger import get_logger
from workflow.workflow import ProjectManagementWorkflow
from workflow.models import WorkflowRequest, WorkflowResponse

router = APIRouter(prefix="/workflow", tags=["Workflow"])

logger = get_logger(__name__)

# ProjectManagementWorkflow 인스턴스 생성
workflow_service = ProjectManagementWorkflow(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@router.post("/execute", response_model=WorkflowResponse)
def execute_workflow(request: WorkflowRequest):
    """프로젝트 관리 워크플로우 동기 실행"""
    try:
        start_time = datetime.now()
        
        result = workflow_service.execute_workflow(request)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"워크플로우 실행 완료 - 총 시간: {execution_time:.2f}초")
        logger.info(f"결과: 에픽 {result.total_epics}개, 스토리 {result.total_stories}개, 추정 {result.total_estimations}개")
        for i, epic_result in enumerate(result.epic_results):
            logger.info(f"에픽 {i+1}: '{epic_result.epic.title}' - 스토리 {len(epic_result.stories)}개, 추정 {len(epic_result.story_point_estimations)}개")
        
        return result
        
    except Exception as e:
        logger.error(f"워크플로우 실행 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/status")
def get_agents_status():
    """각 에이전트의 상태 조회"""
    try:
        return {
            "epic_agent": {
                "status": "healthy"
            },
            "story_agent": {
                "status": "healthy"
            },
            "story_point_agent": {
                "reference_data_loaded": workflow_service.story_point_agent.reference_data is not None,
                "csv_file_path": workflow_service.story_point_agent.csv_file_path,
                "status": "healthy"
            },
            "workflow": {
                "status": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"에이전트 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
def test_workflow():
    """워크플로우 테스트용 엔드포인트"""
    test_request = WorkflowRequest(
        user_input="사용자 인증 및 권한 관리 시스템을 개발해주세요",
        project_info="웹 애플리케이션 프로젝트",
        max_epics=2,
        max_stories_per_epic=3
    )
    
    try:
        result = workflow_service.execute_workflow(test_request)
        return {
            "test_status": "success",
            "result_summary": {
                "epics_count": result.total_epics,
                "stories_count": result.total_stories,
                "estimations_count": result.total_estimations,
                "execution_time": result.execution_time,
                "workflow_status": result.workflow_status,
                "epic_breakdown": [
                    {
                        "epic_title": epic_result.epic.title,
                        "stories_count": len(epic_result.stories),
                        "estimations_count": len(epic_result.story_point_estimations)
                    }
                    for epic_result in result.epic_results
                ]
            }
        }
    except Exception as e:
        logger.error(f"워크플로우 테스트 오류: {str(e)}")
        return {
            "test_status": "failed",
            "error": str(e)
        }

