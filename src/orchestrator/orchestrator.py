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
        """전체 워크플로우 실행"""
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

    def execute_from_step(self, start_step: str, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """특정 단계부터 워크플로우 실행"""
        logger.info(f"단계별 워크플로우 실행 시작: {start_step}")

        try:
            # 상태 복원
            current_state = self._restore_state(state_data, start_step)

            # 지정된 단계부터 실행
            if start_step == "epic":
                final_state = self._execute_from_epic(current_state)
            elif start_step == "story":
                final_state = self._execute_from_story(current_state)
            elif start_step == "point":
                final_state = self._execute_from_point(current_state)
            else:
                raise ValueError(f"지원하지 않는 시작 단계: {start_step}")

            # 결과 포맷팅
            result = self._format_result(final_state)

            logger.info(f"단계별 워크플로우 실행 완료: {start_step}")
            return result

        except Exception as e:
            logger.error(f"단계별 워크플로우 실행 오류: {str(e)}")
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

    def execute_next_step(self, current_state_data: Dict[str, Any]) -> Dict[str, Any]:
        """현재 상태에서 다음 단계만 실행"""
        logger.info("다음 단계 실행 시작")

        try:
            # 현재 상태 복원
            current_state = self._restore_state(current_state_data)

            # 다음 단계 결정
            next_step = self._determine_next_step(current_state)
            if not next_step:
                return self._format_result(current_state)

            # 단일 단계 실행
            if next_step == "epic":
                updated_state = epic_agent_node(current_state)
            elif next_step == "story":
                updated_state = story_agent_node(current_state)
            elif next_step == "point":
                updated_state = story_point_agent_node(current_state)
            else:
                raise ValueError(f"지원하지 않는 다음 단계: {next_step}")

            # 완료 단계 업데이트
            completed_steps = updated_state.get("completed_steps", [])
            if next_step not in completed_steps:
                completed_steps.append(next_step)
                updated_state["completed_steps"] = completed_steps

            result = self._format_result(updated_state)

            logger.info(f"다음 단계 실행 완료: {next_step}")
            return result

        except Exception as e:
            logger.error(f"다음 단계 실행 오류: {str(e)}")
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

    def _restore_state(self, state_data: Dict[str, Any], target_step: str = None) -> OrchestratorState:
        """저장된 데이터에서 상태 복원"""
        logger.info("상태 복원 중")

        # 기본 상태 구조 생성
        restored_state: OrchestratorState = {
            "user_input": state_data.get("user_input", ""),
            "project_info": state_data.get("project_info", ""),
            "workflow_type": state_data.get("workflow_type", "full_pipeline"),
            "required_steps": state_data.get("required_steps", ["epic", "story", "point"]),
            "epics": state_data.get("epics", []),
            "stories": state_data.get("stories", []),
            "story_points": state_data.get("story_points", []),
            "current_step": target_step or state_data.get("current_step", ""),
            "completed_steps": state_data.get("completed_steps", []),
            "errors": state_data.get("errors", []),
            "execution_start_time": datetime.now(),
            "step_times": state_data.get("step_times", {}),
            "next_action": target_step or "epic"
        }

        return restored_state

    def _execute_from_epic(self, state: OrchestratorState) -> OrchestratorState:
        """에픽 단계부터 전체 워크플로우 실행"""
        # 에픽 생성
        state = epic_agent_node(state)
        state["completed_steps"] = state.get("completed_steps", []) + ["epic"]

        # 스토리 생성
        state = story_agent_node(state)
        state["completed_steps"] = state.get("completed_steps", []) + ["story"]

        # 스토리 포인트 추정
        state = story_point_agent_node(state)
        state["completed_steps"] = state.get("completed_steps", []) + ["point"]

        return self._finalize_node(state)

    def _execute_from_story(self, state: OrchestratorState) -> OrchestratorState:
        """스토리 단계부터 워크플로우 실행"""
        # 스토리 생성
        state = story_agent_node(state)
        state["completed_steps"] = state.get("completed_steps", []) + ["story"]

        # 스토리 포인트 추정
        state = story_point_agent_node(state)
        state["completed_steps"] = state.get("completed_steps", []) + ["point"]

        return self._finalize_node(state)

    def _execute_from_point(self, state: OrchestratorState) -> OrchestratorState:
        """스토리 포인트 단계부터 워크플로우 실행"""
        # 스토리 포인트 추정
        state = story_point_agent_node(state)
        state["completed_steps"] = state.get("completed_steps", []) + ["point"]

        return self._finalize_node(state)

    def _determine_next_step(self, state: OrchestratorState) -> str:
        """현재 상태에서 다음 실행할 단계 결정"""
        completed_steps = state.get("completed_steps", [])

        # 단계별 우선순위에 따라 다음 단계 결정
        if "epic" not in completed_steps:
            return "epic"
        elif "story" not in completed_steps:
            return "story"
        elif "point" not in completed_steps:
            return "point"
        else:
            return None  # 모든 단계 완료

    def get_workflow_status(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 현재 상태 조회"""
        completed_steps = state_data.get("completed_steps", [])
        all_steps = ["epic", "story", "point"]

        progress = {
            "completed_steps": completed_steps,
            "remaining_steps": [step for step in all_steps if step not in completed_steps],
            "progress_percentage": (len(completed_steps) / len(all_steps)) * 100,
            "can_continue": len(completed_steps) < len(all_steps),
            "next_step": self._determine_next_step(state_data)
        }

        return progress
    
    def _format_result(self, state: OrchestratorState) -> Dict[str, Any]:
        """결과를 API 응답 형식으로 포맷팅"""
        
        epics = state.get("epics", [])
        stories = state.get("stories", [])
        story_points = state.get("story_points", [])
        errors = state.get("errors", [])
        
        # 에픽별로 스토리와 포인트 그룹화
        epic_results = []
        used_story_points = set()  # 중복 방지를 위한 집합
        
        for epic in epics:
            # 해당 에픽의 스토리들 찾기
            epic_stories = []
            epic_story_points = []
            
            for story in stories:
                if hasattr(story, 'epic_id') and story.epic_id == epic.id:
                    epic_stories.append(story)
                    
                    # 해당 스토리의 포인트들 찾기 (중복 제거)
                    for point in story_points:
                        # 동일한 스토리 타이틀과 포인트 ID로 중복 확인
                        point_key = (point.story_title, getattr(point, 'id', id(point)))
                        if point.story_title == story.title and point_key not in used_story_points:
                            epic_story_points.append(point)
                            used_story_points.add(point_key)
            
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