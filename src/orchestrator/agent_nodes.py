# orchestrator/agent_nodes.py
import logging
import os
from datetime import datetime

from epic.services import EpicGeneratorAgent
from epic.models import EpicRequest
from story.services import StoryGeneratorAgent
from story.models import StoryRequest
from story_point.services import StoryPointEstimationAgent
from story_point.models import StoryPointRequest

from .state_schema import OrchestratorState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 에이전트 인스턴스들 (싱글톤으로 관리)
_epic_agent = None
_story_agent = None
_story_point_agent = None


def _get_epic_agent():
    global _epic_agent
    if _epic_agent is None:
        _epic_agent = EpicGeneratorAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
    return _epic_agent


def _get_story_agent():
    global _story_agent
    if _story_agent is None:
        _story_agent = StoryGeneratorAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
    return _story_agent


def _get_story_point_agent():
    global _story_point_agent
    if _story_point_agent is None:
        _story_point_agent = StoryPointEstimationAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
    return _story_point_agent


def epic_agent_node(state: OrchestratorState) -> OrchestratorState:
    """Epic 생성 에이전트 노드"""
    step_start = datetime.now()
    logger.info("Epic 생성 노드 시작")
    
    try:
        # Epic 생성 요청 준비
        epic_request = EpicRequest(
            user_input=state["user_input"],
            project_info=state.get("project_info", ""),
            max_epics=5  # 기본값
        )
        
        # Epic 생성 실행
        epic_agent = _get_epic_agent()
        epics = epic_agent.generate_epics(epic_request)
        
        logger.info(f"Epic 생성 완료: {len(epics) if epics else 0}개")
        
        # 상태 업데이트
        completed_steps = list(state.get("completed_steps", []))
        if "epic" not in completed_steps:
            completed_steps.append("epic")
        
        step_times = dict(state.get("step_times", {}))
        step_times["epic"] = (datetime.now() - step_start).total_seconds()
        
        return {
            **state,
            "epics": epics if epics else [],
            "current_step": "epic",
            "completed_steps": completed_steps,
            "step_times": step_times,
            "next_action": "epic"  # 매니저가 다음 단계 결정
        }
        
    except Exception as e:
        logger.error(f"Epic 생성 오류: {str(e)}")
        
        # 에러 발생시 기본 에픽 생성 (테스트용)
        from epic.models import Epic
        fallback_epic = Epic(
            title="기본 에픽",
            description=f"에픽 생성에 실패하여 기본 에픽을 생성했습니다. 사용자 요청: {state['user_input']}",
            business_value="기본 비즈니스 가치",
            priority="Medium",
            acceptance_criteria=["기본 기능이 정상적으로 동작한다"],
            included_tasks=["기본 작업"]
        )
        
        completed_steps = list(state.get("completed_steps", []))
        if "epic" not in completed_steps:
            completed_steps.append("epic")
        
        step_times = dict(state.get("step_times", {}))
        step_times["epic"] = (datetime.now() - step_start).total_seconds()
        
        return {
            **state,
            "epics": [fallback_epic],
            "current_step": "epic",
            "completed_steps": completed_steps,
            "errors": state.get("errors", []) + [f"Epic 생성 오류 (기본값 사용): {str(e)}"],
            "step_times": step_times,
            "next_action": "epic"
        }


def story_agent_node(state: OrchestratorState) -> OrchestratorState:
    """Story 생성 에이전트 노드"""
    step_start = datetime.now()
    logger.info("Story 생성 노드 시작")
    
    try:
        epics = state.get("epics", [])
        if not epics:
            raise ValueError("Story 생성을 위한 Epic이 없습니다")
        
        story_agent = _get_story_agent()
        all_stories = []
        
        # 각 Epic에 대해 Story 생성
        for epic in epics:
            story_request = StoryRequest(
                user_input=state["user_input"],
                epic_info=epic,
                max_storys=5  # 기본값
            )
            
            stories = story_agent.generate_storys(story_request)
            
            if stories:
                # Story 객체로 변환하고 epic_id 설정
                for story_data in stories:
                    if isinstance(story_data, dict):
                        # 딕셔너리인 경우 Story 객체로 변환
                        from story.models import Story
                        story = Story(
                            title=story_data.get('title', '제목 없음'),
                            description=story_data.get('description', '설명 없음'),
                            acceptance_criteria=story_data.get('acceptance_criteria', []),
                            domain=story_data.get('domain', 'fullstack'),
                            story_type=story_data.get('story_type', 'feature'),
                            tags=story_data.get('tags', [])
                        )
                        story.epic_id = epic.id
                        all_stories.append(story)
                    else:
                        # 이미 Story 객체인 경우
                        story_data.epic_id = epic.id
                        all_stories.append(story_data)
        
        logger.info(f"Story 생성 완료: {len(all_stories)}개")
        
        # 상태 업데이트
        completed_steps = list(state.get("completed_steps", []))
        if "story" not in completed_steps:
            completed_steps.append("story")
        
        step_times = dict(state.get("step_times", {}))
        step_times["story"] = (datetime.now() - step_start).total_seconds()
        
        return {
            **state,
            "stories": all_stories,
            "current_step": "story",
            "completed_steps": completed_steps,
            "step_times": step_times,
            "next_action": "story"
        }
        
    except Exception as e:
        logger.error(f"Story 생성 오류: {str(e)}")
        
        completed_steps = list(state.get("completed_steps", []))
        if "story" not in completed_steps:
            completed_steps.append("story")
        
        step_times = dict(state.get("step_times", {}))
        step_times["story"] = (datetime.now() - step_start).total_seconds()
        
        return {
            **state,
            "stories": [],
            "current_step": "story",
            "completed_steps": completed_steps,
            "errors": state.get("errors", []) + [f"Story 생성 오류: {str(e)}"],
            "step_times": step_times,
            "next_action": "story"
        }


def story_point_agent_node(state: OrchestratorState) -> OrchestratorState:
    """Story Point 추정 에이전트 노드"""
    step_start = datetime.now()
    logger.info("Story Point 추정 노드 시작")
    
    try:
        stories = state.get("stories", [])
        epics = state.get("epics", [])
        
        if not stories:
            raise ValueError("Story Point 추정을 위한 Story가 없습니다")
        
        story_point_agent = _get_story_point_agent()
        all_estimations = []
        
        # Epic ID로 매핑
        epic_map = {epic.id: epic for epic in epics} if epics else {}
        
        # 각 Story에 대해 Point 추정
        for story in stories:
            try:
                # 해당 Story의 Epic 찾기
                epic_info = None
                if hasattr(story, 'epic_id') and story.epic_id:
                    epic_info = epic_map.get(story.epic_id)
                
                story_point_request = StoryPointRequest(
                    user_input=state["user_input"],
                    epic_info=epic_info,
                    story_info=story,
                    reference_stories=[]
                )
                
                estimations = story_point_agent.estimate_story_points(story_point_request)
                
                if estimations:
                    all_estimations.extend(estimations)
                    logger.info(f"Story '{story.title}' 포인트 추정 완료: {len(estimations)}개")
                
            except Exception as e:
                logger.warning(f"Story '{story.title}' 포인트 추정 실패: {str(e)}")
                continue
        
        logger.info(f"Story Point 추정 완료: {len(all_estimations)}개")
        
        # 상태 업데이트
        completed_steps = list(state.get("completed_steps", []))
        if "point" not in completed_steps:
            completed_steps.append("point")
        
        step_times = dict(state.get("step_times", {}))
        step_times["point"] = (datetime.now() - step_start).total_seconds()
        
        return {
            **state,
            "story_points": all_estimations,
            "current_step": "point",
            "completed_steps": completed_steps,
            "step_times": step_times,
            "next_action": "point"
        }
        
    except Exception as e:
        logger.error(f"Story Point 추정 오류: {str(e)}")
        
        completed_steps = list(state.get("completed_steps", []))
        if "point" not in completed_steps:
            completed_steps.append("point")
        
        step_times = dict(state.get("step_times", {}))
        step_times["point"] = (datetime.now() - step_start).total_seconds()
        
        return {
            **state,
            "story_points": [],
            "current_step": "point",
            "completed_steps": completed_steps,
            "errors": state.get("errors", []) + [f"Story Point 추정 오류: {str(e)}"],
            "step_times": step_times,
            "next_action": "point"
        }


def initialize_node(state: OrchestratorState) -> OrchestratorState:
    """워크플로우 초기화 노드"""
    logger.info("워크플로우 초기화 노드 시작")
    
    return {
        **state,
        "current_step": "initialize",
        "completed_steps": [],
        "errors": [],
        "execution_start_time": datetime.now(),
        "step_times": {},
        "next_action": "analyze"
    }