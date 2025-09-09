# orchestrator/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional, List

from utils.logger import get_logger
from .orchestrator import get_orchestrator

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])

logger = get_logger(__name__)


# 요청/응답 모델
class OrchestratorRequest(BaseModel):
    """오케스트레이터 실행 요청"""
    user_input: str = Field(..., description="사용자 입력")
    project_info: Optional[str] = Field("", description="프로젝트 정보")


class OrchestratorResponse(BaseModel):
    """오케스트레이터 실행 응답"""
    status: str = Field(..., description="실행 상태")
    workflow_type: str = Field(..., description="워크플로우 타입")
    epic_results: List[Dict[str, Any]] = Field(..., description="에픽별 결과")
    total_epics: int = Field(..., description="총 에픽 수")
    total_stories: int = Field(..., description="총 스토리 수")
    total_story_points: int = Field(..., description="총 스토리 포인트 수")
    execution_time: float = Field(..., description="실행 시간(초)")
    step_times: Dict[str, float] = Field(..., description="단계별 실행 시간")
    completed_steps: List[str] = Field(..., description="완료된 단계들")
    errors: List[str] = Field(..., description="에러 목록")


@router.post("/execute", response_model=OrchestratorResponse)
def execute_workflow(request: OrchestratorRequest):
    """메인 워크플로우 실행 엔드포인트"""
    try:
        start_time = datetime.now()
        
        logger.info(f"오케스트레이터 실행 시작: {request.user_input}")
        
        # 오케스트레이터 실행
        orchestrator = get_orchestrator()
        result = orchestrator.execute(
            user_input=request.user_input,
            project_info=request.project_info
        )
        
        end_time = datetime.now()
        api_execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"오케스트레이터 실행 완료 - API 시간: {api_execution_time:.2f}초")
        logger.info(f"결과: 상태={result['status']}, 에픽={result['total_epics']}, 스토리={result['total_stories']}, 포인트={result['total_story_points']}")
        
        return OrchestratorResponse(**result)
        
    except Exception as e:
        logger.error(f"오케스트레이터 실행 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    """오케스트레이터 헬스 체크"""
    try:
        orchestrator = get_orchestrator()
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "orchestrator": "active",
            "graph_compiled": orchestrator.graph is not None
        }
    except Exception as e:
        logger.error(f"헬스 체크 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow-types")
def get_workflow_types():
    """지원하는 워크플로우 타입 목록"""
    return {
        "workflow_types": [
            {
                "type": "epic_only",
                "description": "에픽 생성만 수행",
                "example": "프로젝트를 큰 기능 단위로 나눠줘"
            },
            {
                "type": "story_only", 
                "description": "스토리 생성만 수행",
                "example": "이 에픽에 대한 상세 스토리를 만들어줘"
            },
            {
                "type": "point_only",
                "description": "스토리 포인트 추정만 수행", 
                "example": "이 스토리들의 개발 시간을 추정해줘"
            },
            {
                "type": "full_pipeline",
                "description": "에픽 → 스토리 → 포인트 전체 파이프라인 수행",
                "example": "프로젝트를 완전히 분석해서 개발 계획을 세워줘"
            }
        ]
    }


@router.get("/test")
def test_orchestrator():
    """오케스트레이터 테스트용 엔드포인트"""
    test_request = OrchestratorRequest(
        user_input="사용자 인증 시스템을 만들어주세요",
        project_info="웹 애플리케이션"
    )
    
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.execute(
            user_input=test_request.user_input,
            project_info=test_request.project_info
        )
        
        return {
            "test_status": "success",
            "result_summary": {
                "status": result["status"],
                "workflow_type": result["workflow_type"],
                "total_epics": result["total_epics"],
                "total_stories": result["total_stories"], 
                "total_story_points": result["total_story_points"],
                "execution_time": result["execution_time"],
                "errors_count": len(result["errors"])
            }
        }
        
    except Exception as e:
        logger.error(f"오케스트레이터 테스트 오류: {str(e)}")
        return {
            "test_status": "failed",
            "error": str(e)
        }


@router.get("/test-mock")
def test_orchestrator_mock():
    """Mock 데이터로 오케스트레이터 테스트"""
    from epic.models import Epic
    from story.models import Story
    from story_point.models import StoryPointEstimation
    
    # Mock 데이터 생성
    mock_epic = Epic(
        title="사용자 인증 시스템",
        description="로그인, 회원가입, 권한 관리를 포함한 사용자 인증 시스템",
        business_value="사용자 보안 강화 및 개인화 서비스 제공",
        priority="High",
        acceptance_criteria=[
            "사용자가 이메일로 회원가입할 수 있다",
            "사용자가 로그인/로그아웃할 수 있다", 
            "관리자는 사용자 권한을 관리할 수 있다"
        ],
        included_tasks=["회원가입", "로그인", "권한관리"]
    )
    
    mock_story = Story(
        title="이메일 회원가입 기능",
        description="사용자가 이메일과 비밀번호로 회원가입할 수 있는 기능",
        acceptance_criteria=[
            "이메일 형식 검증",
            "비밀번호 강도 검증",
            "이메일 중복 체크"
        ],
        domain="fullstack",
        story_type="feature",
        tags=["authentication", "signup"]
    )
    mock_story.epic_id = mock_epic.id
    
    mock_estimation = StoryPointEstimation(
        story_title="이메일 회원가입 기능",
        estimated_point=5,
        domain="fullstack", 
        estimation_method="cross_area",
        reasoning="프론트엔드 폼 구현, 백엔드 API, 데이터베이스 스키마 설계가 필요",
        complexity_factors=["UI 구현", "API 개발", "유효성 검증", "데이터베이스"],
        similar_stories=["로그인 기능", "비밀번호 재설정"],
        confidence_level="high",
        assumptions=["기본적인 React/Node.js 스택 사용"],
        risks=["이메일 서비스 연동 복잡도"]
    )
    
    # Mock 결과 구성
    mock_result = {
        "status": "completed",
        "workflow_type": "full_pipeline",
        "epic_results": [
            {
                "epic": mock_epic,
                "stories": [mock_story],
                "story_points": [mock_estimation]
            }
        ],
        "total_epics": 1,
        "total_stories": 1,
        "total_story_points": 1,
        "execution_time": 2.5,
        "step_times": {
            "analyze": 0.3,
            "epic": 0.8,
            "story": 0.9,
            "point": 0.5
        },
        "completed_steps": ["analyze", "epic", "story", "point"],
        "errors": []
    }
    
    return {
        "test_status": "success",
        "data_type": "mock",
        "result": mock_result
    }