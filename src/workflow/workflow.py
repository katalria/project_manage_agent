import logging
import os
from datetime import datetime
from typing import List, Optional

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from epic.services import EpicGeneratorAgent
from epic.models import EpicRequest
from story.services import StoryGeneratorAgent
from story.models import StoryRequest
from story_point.services import StoryPointEstimationAgent
from story_point.models import StoryPointRequest

from workflow.models import ProjectManagementState, WorkflowRequest, WorkflowResponse, EpicWithStoriesAndEstimations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectManagementWorkflow:
    """프로젝트 관리 워크플로우 - Epic → Story → StoryPoint 순차 처리"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        
        # 각 에이전트 초기화
        self.epic_agent = EpicGeneratorAgent(openai_api_key)
        self.story_agent = StoryGeneratorAgent(openai_api_key)
        self.story_point_agent = StoryPointEstimationAgent(openai_api_key)
        
        
        # 워크플로우 그래프 생성
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(ProjectManagementState)
        
        # 노드 추가
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("generate_epics", self._generate_epics)
        workflow.add_node("generate_stories", self._generate_stories)
        workflow.add_node("estimate_story_points", self._estimate_story_points)
        workflow.add_node("finalize", self._finalize_workflow)
        
        # 엣지 추가
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "generate_epics")
        workflow.add_edge("generate_epics", "generate_stories")
        workflow.add_edge("generate_stories", "estimate_story_points")
        workflow.add_edge("estimate_story_points", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _initialize_workflow(self, state: ProjectManagementState) -> ProjectManagementState:
        """워크플로우 초기화"""
        logger.info("워크플로우 초기화 시작")
        
        state["current_step"] = "initialize"
        state["execution_start_time"] = datetime.now()
        state["step_times"] = {}
        state["errors"] = []
        state["generated_epics"] = []
        state["generated_stories"] = []
        state["story_point_estimations"] = []
        
        # Epic 요청 생성
        state["epic_request"] = EpicRequest(
            user_input=state["user_input"],
            project_info=state["project_info"],
            max_epics=state["max_epics"]
        )
        
        logger.info("워크플로우 초기화 완료")
        return state
    
    def _generate_epics(self, state: ProjectManagementState) -> ProjectManagementState:
        """에픽 생성 단계"""
        step_start = datetime.now()
        logger.info("에픽 생성 단계 시작")
        
        state["current_step"] = "generate_epics"
        
        try:
            # 에픽 생성
            epic_request = state["epic_request"]
            logger.info(f"에픽 생성 요청 메세지: {epic_request}")
            epics = self.epic_agent.generate_epics(epic_request)
            
            if not epics:
                error_msg = "에픽 생성 실패"
                state["errors"].append(error_msg)
                logger.error(error_msg)
            else:
                state["generated_epics"] = epics
                logger.info("에픽 생성 완료")
                
        except Exception as e:
            error_msg = f"에픽 생성 중 오류: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
        
        state["step_times"]["generate_epics"] = (datetime.now() - step_start).total_seconds()
        return state
    
    def _generate_stories(self, state: ProjectManagementState) -> ProjectManagementState:
        """스토리 생성 단계"""
        step_start = datetime.now()
        logger.info("스토리 생성 단계 시작")
        
        state["current_step"] = "generate_stories"
        state["story_requests"] = []
        all_stories = []
        
        try:
            epics = state["generated_epics"]
            
            if not epics:
                error_msg = "생성된 에픽이 없어 스토리 생성을 건너뜁니다"
                state["errors"].append(error_msg)
                logger.warning(error_msg)
                return state
            
            # 각 에픽에 대해 스토리 생성
            for epic in epics:
                try:
                    story_request = StoryRequest(
                        user_input=state["user_input"],
                        epic_info=epic,
                        max_storys=state["max_stories_per_epic"]
                    )
                    state["story_requests"].append(story_request)
                    
                    # 스토리 생성
                    stories = self.story_agent.generate_storys(story_request)
                    
                    if stories:
                        # 스토리를 Story 객체로 변환하고 epic_id 설정
                        for story_data in stories:
                            try:
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
                            except Exception as e:
                                logger.warning(f"스토리 변환 실패: {str(e)}")
                                continue
                        
                        logger.info(f"에픽 '{epic.title}'에 대한 스토리 생성 완료: {len(stories)}개")
                    
                except Exception as e:
                    error_msg = f"에픽 '{epic.title}' 스토리 생성 오류: {str(e)}"
                    state["errors"].append(error_msg)
                    logger.error(error_msg)
            
            state["generated_stories"] = all_stories
            logger.info(f"전체 스토리 생성 완료: {len(all_stories)}개")
            
        except Exception as e:
            error_msg = f"스토리 생성 중 오류: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
        
        state["step_times"]["generate_stories"] = (datetime.now() - step_start).total_seconds()
        return state
    
    def _estimate_story_points(self, state: ProjectManagementState) -> ProjectManagementState:
        """스토리 포인트 추정 단계"""
        step_start = datetime.now()
        logger.info("스토리 포인트 추정 단계 시작")
        
        state["current_step"] = "estimate_story_points"
        state["story_point_requests"] = []
        all_estimations = []
        
        try:
            stories = state["generated_stories"]
            epics = state["generated_epics"]
            
            if not stories:
                error_msg = "생성된 스토리가 없어 스토리 포인트 추정을 건너뜁니다"
                state["errors"].append(error_msg)
                logger.warning(error_msg)
                return state
            
            # 에픽 ID로 매핑
            epic_map = {epic.id: epic for epic in epics}
            
            # 각 스토리에 대해 스토리 포인트 추정
            for story in stories:
                try:
                    # 해당 스토리의 에픽 찾기
                    epic_info = None
                    if hasattr(story, 'epic_id') and story.epic_id:
                        epic_info = epic_map.get(story.epic_id)
                    
                    story_point_request = StoryPointRequest(
                        user_input=state["user_input"],
                        epic_info=epic_info,
                        story_info=story,
                        reference_stories=[]
                    )
                    state["story_point_requests"].append(story_point_request)
                    
                    # 스토리 포인트 추정
                    estimations = self.story_point_agent.estimate_story_points(story_point_request)
                    
                    if estimations:
                        all_estimations.extend(estimations)
                        logger.info(f"스토리 '{story.title}' 포인트 추정 완료: {len(estimations)}개")
                    
                except Exception as e:
                    error_msg = f"스토리 '{story.title}' 포인트 추정 오류: {str(e)}"
                    state["errors"].append(error_msg)
                    logger.error(error_msg)
            
            state["story_point_estimations"] = all_estimations
            logger.info(f"전체 스토리 포인트 추정 완료: {len(all_estimations)}개")
            
        except Exception as e:
            error_msg = f"스토리 포인트 추정 중 오류: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
        
        state["step_times"]["estimate_story_points"] = (datetime.now() - step_start).total_seconds()
        return state
    
    def _finalize_workflow(self, state: ProjectManagementState) -> ProjectManagementState:
        """워크플로우 마무리"""
        logger.info("워크플로우 마무리 단계")
        
        state["current_step"] = "finalize"
        
        # 총 실행 시간 계산
        if state["execution_start_time"]:
            total_time = (datetime.now() - state["execution_start_time"]).total_seconds()
            state["step_times"]["total"] = total_time
        
        logger.info("워크플로우 완료")
        logger.info(f"생성된 에픽: {len(state['generated_epics'])}개")
        logger.info(f"생성된 스토리: {len(state['generated_stories'])}개")
        logger.info(f"추정된 스토리 포인트: {len(state['story_point_estimations'])}개")
        
        if state["errors"]:
            logger.warning(f"워크플로우 중 {len(state['errors'])}개 오류 발생")
        
        return state
    
    def execute_workflow(self, request: WorkflowRequest) -> WorkflowResponse:
        """워크플로우 실행 (동기)"""
        start_time = datetime.now()
        
        try:
            # 초기 상태 설정
            initial_state: ProjectManagementState = {
                "user_input": request.user_input,
                "project_info": request.project_info,
                "max_epics": request.max_epics,
                "max_stories_per_epic": request.max_stories_per_epic,
                "epic_request": None,
                "generated_epics": [],
                "story_requests": [],
                "generated_stories": [],
                "story_point_requests": [],
                "story_point_estimations": [],
                "current_step": "",
                "errors": [],
                "execution_start_time": None,
                "step_times": {}
            }
            
            # 워크플로우 실행
            final_state = self.workflow.invoke(initial_state)
            
            # 실행 시간 계산
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 응답 생성 - 에픽별로 그룹화
            epic_results = self._group_results_by_epic(
                final_state["generated_epics"],
                final_state["generated_stories"], 
                final_state["story_point_estimations"]
            )
            
            workflow_status = "completed" if not final_state["errors"] else "completed_with_errors"
            
            return WorkflowResponse(
                epic_results=epic_results,
                total_epics=len(final_state["generated_epics"]),
                total_stories=len(final_state["generated_stories"]),
                total_estimations=len(final_state["story_point_estimations"]),
                execution_time=execution_time,
                workflow_status=workflow_status
            )
            
        except Exception as e:
            logger.error(f"워크플로우 실행 중 오류: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return WorkflowResponse(
                epic_results=[],
                total_epics=0,
                total_stories=0,
                total_estimations=0,
                execution_time=execution_time,
                workflow_status="failed"
            )
    
    def _group_results_by_epic(self, epics, stories, estimations):
        """결과를 에픽별로 그룹화"""
        epic_results = []
        
        logger.info(f"그룹화 시작 - 에픽: {len(epics)}개, 스토리: {len(stories)}개, 추정: {len(estimations)}개")
        
        for epic in epics:
            # 해당 에픽의 스토리들 찾기
            epic_stories = []
            epic_estimations = []
            
            logger.info(f"에픽 '{epic.title}' (ID: {epic.id}) 처리 중...")
            
            for story in stories:
                logger.debug(f"스토리 확인: '{story.title if hasattr(story, 'title') else story}', epic_id: {getattr(story, 'epic_id', None)}")
                
                if hasattr(story, 'epic_id') and story.epic_id == epic.id:
                    epic_stories.append(story)
                    logger.info(f"에픽 '{epic.title}'에 스토리 '{story.title}' 추가됨")
                    
                    # 해당 스토리의 추정 결과들 찾기
                    for estimation in estimations:
                        if estimation.story_title == story.title:
                            epic_estimations.append(estimation)
                            logger.info(f"스토리 '{story.title}'에 추정 결과 추가됨")
            
            logger.info(f"에픽 '{epic.title}' 결과: 스토리 {len(epic_stories)}개, 추정 {len(epic_estimations)}개")
            
            epic_result = EpicWithStoriesAndEstimations(
                epic=epic,
                stories=epic_stories,
                story_point_estimations=epic_estimations
            )
            epic_results.append(epic_result)
        
        return epic_results