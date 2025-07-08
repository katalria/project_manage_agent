import pytest
import tempfile
import csv
from src.services.project_management_orchestrator import ProjectManagementOrchestrator
from src.services.story_point_agent import StoryPointAgent


@pytest.fixture
def sample_tasks():
    return [
        "사용자 로그인 기능 구현",
        "비밀번호 재설정 기능 추가",
        "상품 목록 페이지 개발",
        "장바구니 기능 구현",
        "결제 시스템 연동"
    ]


@pytest.fixture
def sample_reference_csv():
    """테스트용 참고 스토리 CSV 파일을 생성합니다."""
    data = [
        {"title": "로그인 UI 개발", "description": "로그인 화면 UI를 구현합니다", "point": 2, "area": "frontend"},
        {"title": "로그인 API 개발", "description": "로그인 백엔드 API를 구현합니다", "point": 3, "area": "backend"},
        {"title": "상품 리스트 API", "description": "상품 목록을 반환하는 API", "point": 2, "area": "backend"},
        {"title": "장바구니 UI", "description": "장바구니 화면 구현", "point": 5, "area": "frontend"},
        {"title": "결제 모듈 연동", "description": "외부 결제 시스템과 연동", "point": 8, "area": "integration"}
    ]
    
    # 임시 CSV 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=["title", "description", "point", "area"])
        writer.writeheader()
        writer.writerows(data)
        return f.name


class TestStoryPointAgent:
    def test_load_reference_csv(self, sample_reference_csv):
        """CSV 파일 로드 테스트"""
        agent = StoryPointAgent()
        success = agent.load_reference_csv(sample_reference_csv)
        assert success
        assert agent.reference_data is not None
        assert len(agent.reference_data) == 5
    
    def test_get_reference_stories_by_area(self, sample_reference_csv):
        """영역별 참고 스토리 조회 테스트"""
        agent = StoryPointAgent()
        agent.load_reference_csv(sample_reference_csv)
        
        backend_stories = agent.get_reference_stories_by_area("backend")
        assert len(backend_stories) == 2
        
        frontend_stories = agent.get_reference_stories_by_area("frontend")
        assert len(frontend_stories) == 2
        
        unknown_stories = agent.get_reference_stories_by_area("unknown")
        assert len(unknown_stories) == 0


class TestProjectManagementOrchestrator:
    def test_initialization(self):
        """오케스트레이터 초기화 테스트"""
        orchestrator = ProjectManagementOrchestrator()
        assert orchestrator.epic_agent is not None
        assert orchestrator.point_agent is not None
    
    def test_load_reference_data(self, sample_reference_csv):
        """참고 데이터 로드 테스트"""
        orchestrator = ProjectManagementOrchestrator()
        success = orchestrator.load_reference_data(sample_reference_csv)
        assert success
        assert orchestrator.point_agent.reference_data is not None
    
    def test_get_estimation_summary_structure(self):
        """추정 요약 정보 구조 테스트"""
        orchestrator = ProjectManagementOrchestrator()
        
        # 테스트용 데이터
        test_data = {
            "epics": [
                {
                    "epic": {"title": "Test Epic"},
                    "stories": [
                        {
                            "title": "Test Story 1",
                            "point": 3,
                            "area": "backend",
                            "confidence_level": "high"
                        },
                        {
                            "title": "Test Story 2", 
                            "point": 5,
                            "area": "frontend",
                            "confidence_level": "medium"
                        }
                    ]
                }
            ]
        }
        
        summary = orchestrator.get_estimation_summary(test_data)
        
        assert "total_epics" in summary
        assert "total_stories" in summary
        assert "total_story_points" in summary
        assert "area_breakdown" in summary
        assert "confidence_distribution" in summary
        assert "average_points_per_story" in summary
        
        assert summary["total_epics"] == 1
        assert summary["total_stories"] == 2
        assert summary["total_story_points"] == 8
        assert summary["average_points_per_story"] == 4.0


@pytest.mark.asyncio
async def test_basic_integration():
    """기본 통합 테스트 (실제 LLM 호출 없이)"""
    orchestrator = ProjectManagementOrchestrator()
    
    # 오케스트레이터가 정상적으로 초기화되는지 확인
    assert orchestrator is not None
    assert hasattr(orchestrator, 'epic_agent')
    assert hasattr(orchestrator, 'point_agent')
    assert hasattr(orchestrator, 'load_reference_data')
    assert hasattr(orchestrator, 'process_tasks_with_estimation')


def test_story_point_validation():
    """스토리 포인트 유효성 검증 테스트"""
    agent = StoryPointAgent()
    
    # 유효한 포인트 값들
    valid_points = [1, 2, 3, 5, 8]
    
    # 파싱 테스트용 응답
    test_responses = [
        '{"estimated_point": 3, "reasoning": "test", "complexity_factors": [], "similar_stories": [], "confidence_level": "medium"}',
        '{"estimated_point": 10, "reasoning": "test", "complexity_factors": [], "similar_stories": [], "confidence_level": "medium"}',  # 잘못된 값
        'invalid json'
    ]
    
    for response in test_responses:
        result = agent.parse_estimation_response(response)
        assert result["estimated_point"] in valid_points
        assert "reasoning" in result
        assert "confidence_level" in result