import logging

from .state_schema import OrchestratorState

logger = logging.getLogger(__name__)


def manager_node(state: OrchestratorState) -> OrchestratorState:
    """
    QueryAnalyzer 결과를 기반으로 조건부 라우팅을 수행하는 개선된 매니저
    """
    logger.info("매니저 노드 시작")
    
    try:
        # 필요한 단계와 완료된 단계 확인
        required_steps = state.get("required_steps", [])
        completed_steps = state.get("completed_steps", [])
        workflow_type = state.get("workflow_type", "full_pipeline")
        
        logger.info(f"워크플로우 타입: {workflow_type}")
        logger.info(f"필요한 단계: {required_steps}")
        logger.info(f"완료된 단계: {completed_steps}")
        
        # 다음 실행할 단계 찾기
        next_step = None
        for step in required_steps:
            if step not in completed_steps:
                next_step = step
                break
        
        # 모든 단계가 완료된 경우
        if next_step is None:
            logger.info("모든 단계 완료, 워크플로우 종료")
            return {
                **state,
                "next_action": "done",
                "current_step": "completed"
            }
        
        # 워크플로우 타입별 특별 처리
        next_action = _determine_next_action(next_step, workflow_type, state)
        
        logger.info(f"다음 액션: {next_action}")
        
        return {
            **state,
            "next_action": next_action,
            "current_step": f"routing_to_{next_step}"
        }
        
    except Exception as e:
        logger.error(f"매니저 노드 오류: {str(e)}")
        return {
            **state,
            "next_action": "done",
            "current_step": "error",
            "errors": state.get("errors", []) + [f"매니저 오류: {str(e)}"]
        }


def _determine_next_action(next_step: str, workflow_type: str, state: OrchestratorState) -> str:
    """워크플로우 타입과 다음 단계에 따라 액션 결정"""
    
    # 기본 매핑
    step_to_action = {
        "epic": "epic",
        "story": "story", 
        "point": "point"
    }
    
    action = step_to_action.get(next_step, "done")
    
    # 워크플로우 타입별 특별한 검증
    if workflow_type == "story_only" and action == "story":
        # 스토리만 생성하는 경우, 에픽 정보가 있는지 확인
        if not state.get("epics"):
            logger.warning("스토리 생성을 위한 에픽 정보가 없음")
            # 에픽 정보가 없으면 에픽부터 생성
            return "epic"
    
    elif workflow_type == "point_only" and action == "point":
        # 포인트만 추정하는 경우, 스토리 정보가 있는지 확인
        if not state.get("stories"):
            logger.warning("포인트 추정을 위한 스토리 정보가 없음")
            # 스토리 정보가 없으면 스토리부터 생성
            return "story"
    
    return action


# 기존 호환성을 위한 함수
def manager_node_legacy(state) -> dict:
    """기존 코드 호환성을 위한 레거시 매니저"""
    if "epics" not in state:
        return {**state, "next_action": "epic"}
    elif "stories" not in state:
        return {**state, "next_action": "story"}
    elif "points" not in state:
        return {**state, "next_action": "point"}
    else:
        return {**state, "next_action": "done"}
