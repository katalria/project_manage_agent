from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from uuid import uuid4
import os

from utils.logger import get_logger
from workflow.workflow import ProjectManagementWorkflow
from workflow.models import WorkflowRequest, WorkflowResponse, WorkflowProcessingStatus

router = APIRouter(prefix="/workflow", tags=["Workflow"])

logger = get_logger(__name__)

# ProjectManagementWorkflow 인스턴스 생성
workflow_service = ProjectManagementWorkflow(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest):
    """프로젝트 관리 워크플로우 동기 실행"""
    try:
        start_time = datetime.now()
        
        result = await workflow_service.execute_workflow(request)
        
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


@router.post("/execute-async")
async def execute_workflow_async(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """프로젝트 관리 워크플로우 비동기 실행"""
    try:
        task_id = str(uuid4())
        
        # 초기 상태 설정
        workflow_service.processing_tasks[task_id] = WorkflowProcessingStatus(
            task_id=task_id,
            status="pending",
            current_step="initialize",
            message="워크플로우 실행 대기 중...",
            progress=0
        )
        
        # 백그라운드 태스크 추가
        background_tasks.add_task(
            workflow_service.execute_workflow_async, 
            request, 
            task_id
        )
        
        return {
            "task_id": task_id, 
            "message": "프로젝트 관리 워크플로우 작업이 시작되었습니다.",
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"비동기 워크플로우 실행 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """워크플로우 작업 상태 조회"""
    status = workflow_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    return status


@router.get("/agents/status")
async def get_agents_status():
    """각 에이전트의 상태 조회"""
    try:
        return {
            "epic_agent": {
                "active_tasks": len(workflow_service.epic_agent.processing_tasks),
                "status": "healthy"
            },
            "story_agent": {
                "active_tasks": len(workflow_service.story_agent.processing_tasks),
                "status": "healthy"
            },
            "story_point_agent": {
                "active_tasks": len(workflow_service.story_point_agent.processing_tasks),
                "reference_data_loaded": workflow_service.story_point_agent.reference_data is not None,
                "csv_file_path": workflow_service.story_point_agent.csv_file_path,
                "status": "healthy"
            },
            "workflow": {
                "active_workflows": len(workflow_service.processing_tasks),
                "status": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"에이전트 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_workflow():
    """워크플로우 테스트용 엔드포인트"""
    test_request = WorkflowRequest(
        user_input="사용자 인증 및 권한 관리 시스템을 개발해주세요",
        project_info="웹 애플리케이션 프로젝트",
        max_epics=2,
        max_stories_per_epic=3
    )
    
    try:
        result = await workflow_service.execute_workflow(test_request)
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


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "workflow_service": "active",
        "agents": {
            "epic": "initialized",
            "story": "initialized", 
            "story_point": "initialized"
        }
    }