# orchestrator/orchestrator.py
import logging
from datetime import datetime
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from .state_schema import OrchestratorState
from .query_analyzer import query_analyzer_node
from .manager import manager_node
from .agent_nodes import initialize_node, epic_agent_node, story_agent_node, story_point_agent_node

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectManagementOrchestrator:
    """LangGraph 기반 프로젝트 관리 오케스트레이터"""
    
    def __init__(self):
        self.graph = self._create_graph()
        logger.info("프로젝트 관리 오케스트레이터 초기화 완료")
    
    def _create_graph(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        
        # StateGraph 생성
        workflow = StateGraph(OrchestratorState)
        
        # 노드 추가
        workflow.add_node("initialize", initialize_node)
        workflow.add_node("analyze", query_analyzer_node)
        workflow.add_node("manager", manager_node)
        workflow.add_node("epic", epic_agent_node)
        workflow.add_node("story", story_agent_node)
        workflow.add_node("point", story_point_agent_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # 진입점 설정
        workflow.set_entry_point("initialize")
        
        # 고정 엣지 (순서가 정해진 것들)
        workflow.add_edge("initialize", "analyze")
        workflow.add_edge("analyze", "manager")
        
        # 조건부 엣지 (Manager에서 next_action에 따라 분기)
        workflow.add_conditional_edges(
            "manager",
            self._route_next_action,
            {
                "epic": "epic",
                "story": "story", 
                "point": "point",
                "done": "finalize",
                "END": END
            }
        )
        
        # 각 에이전트 노드에서 매니저로 다시 돌아가기
        workflow.add_edge("epic", "manager")
        workflow.add_edge("story", "manager")
        workflow.add_edge("point", "manager")
        
        # 종료
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _route_next_action(self, state: OrchestratorState) -> str:
        """next_action에 따른 라우팅 결정"""
        next_action = state.get("next_action", "done")
        logger.info(f"라우팅 결정: {next_action}")
        
        # 에러가 있거나 완료된 경우
        if state.get("errors") and len(state.get("errors", [])) > 3:
            logger.warning("에러가 너무 많아 워크플로우 중단")
            return "done"
        
        if next_action == "done":
            return "done"
        elif next_action in ["epic", "story", "point"]:
            return next_action
        else:
            logger.warning(f"알 수 없는 next_action: {next_action}, 종료합니다")
            return "done"
    
    def _finalize_node(self, state: OrchestratorState) -> OrchestratorState:
        """워크플로우 완료 처리 노드"""
        logger.info("워크플로우 완료 처리 시작")
        
        execution_time = 0
        if state.get("execution_start_time"):
            execution_time = (datetime.now() - state["execution_start_time"]).total_seconds()
        
        return {
            **state,
            "current_step": "finalized",
            "next_action": "done",
            "execution_time": execution_time
        }
    
    def execute(self, user_input: str, project_info: str = "") -> Dict[str, Any]:
        """워크플로우 실행"""
        logger.info(f"워크플로우 실행 시작: {user_input}")
        
        try:
            # 초기 상태 설정
            initial_state: OrchestratorState = {
                "user_input": user_input,
                "project_info": project_info
            }
            
            # 워크플로우 실행
            final_state = self.graph.invoke(initial_state)
            
            # 결과 포맷팅
            result = self._format_result(final_state)
            
            logger.info("워크플로우 실행 완료")
            return result
            
        except Exception as e:
            logger.error(f"워크플로우 실행 오류: {str(e)}")
            return {
                "status": "error",
                "workflow_type": "unknown",
                "epic_results": [],
                "total_epics": 0,
                "total_stories": 0,
                "total_story_points": 0,
                "execution_time": 0,
                "step_times": {},
                "completed_steps": [],
                "errors": [str(e)]
            }
    
    def _format_result(self, state: OrchestratorState) -> Dict[str, Any]:
        """결과를 API 응답 형식으로 포맷팅"""
        
        epics = state.get("epics", [])
        stories = state.get("stories", [])
        story_points = state.get("story_points", [])
        errors = state.get("errors", [])
        
        # 에픽별로 스토리와 포인트 그룹화
        epic_results = []
        
        for epic in epics:
            # 해당 에픽의 스토리들 찾기
            epic_stories = []
            epic_story_points = []
            
            for story in stories:
                if hasattr(story, 'epic_id') and story.epic_id == epic.id:
                    epic_stories.append(story)
                    
                    # 해당 스토리의 포인트들 찾기
                    for point in story_points:
                        if point.story_title == story.title:
                            epic_story_points.append(point)
            
            epic_result = {
                "epic": epic,
                "stories": epic_stories,
                "story_points": epic_story_points
            }
            epic_results.append(epic_result)
        
        status = "completed"
        if errors:
            status = "completed_with_errors" if epics or stories or story_points else "failed"
        
        return {
            "status": status,
            "workflow_type": state.get("workflow_type", "unknown"),
            "epic_results": epic_results,
            "total_epics": len(epics),
            "total_stories": len(stories),
            "total_story_points": len(story_points),
            "execution_time": state.get("execution_time", 0),
            "step_times": state.get("step_times", {}),
            "completed_steps": state.get("completed_steps", []),
            "errors": errors
        }


# 싱글톤 인스턴스
_orchestrator_instance = None


def get_orchestrator() -> ProjectManagementOrchestrator:
    """오케스트레이터 싱글톤 인스턴스 반환"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ProjectManagementOrchestrator()
    return _orchestrator_instance