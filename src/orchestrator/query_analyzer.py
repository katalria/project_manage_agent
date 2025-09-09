# orchestrator/query_analyzer.py
import logging
from datetime import datetime
from typing import List

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from .state_schema import OrchestratorState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


QUERY_ANALYSIS_PROMPT = ChatPromptTemplate.from_template(
    """사용자의 요청을 분석하여 어떤 워크플로우가 필요한지 결정해주세요.

사용자 입력: {user_input}

아래 옵션 중 하나를 선택하고 그 이유를 설명해주세요:

1. "epic_only" - 에픽 생성만 필요한 경우
   예: "프로젝트 에픽을 생성해줘", "큰 기능 단위로 나눠줘"

2. "story_only" - 스토리 생성만 필요한 경우  
   예: "이 에픽에 대한 스토리를 만들어줘", "상세 기능을 나눠줘"

3. "point_only" - 스토리 포인트 추정만 필요한 경우
   예: "이 스토리의 포인트를 추정해줘", "개발 시간을 예측해줘"

4. "full_pipeline" - 전체 파이프라인이 필요한 경우
   예: "프로젝트를 완전히 분석해줘", "에픽부터 포인트까지 모든 걸 해줘"

응답 형식:
{{
    "workflow_type": "선택한_타입",
    "reasoning": "선택 이유",
    "required_steps": ["단계1", "단계2", ...]
}}

단계는 다음 중에서 선택:
- "epic" (에픽 생성)
- "story" (스토리 생성)  
- "point" (포인트 추정)
"""
)


def query_analyzer_node(state: OrchestratorState) -> OrchestratorState:
    """사용자 쿼리를 분석하여 워크플로우 타입을 결정하는 노드"""
    
    start_time = datetime.now()
    logger.info("쿼리 분석 시작")
    
    try:
        # LLM 초기화 (환경 변수에서 API 키 가져와야 함)
        import os
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # 쿼리 분석 실행
        user_input = state["user_input"]
        prompt = QUERY_ANALYSIS_PROMPT.format(user_input=user_input)
        
        response = llm.invoke(prompt)
        analysis_result = response.content
        
        logger.info(f"LLM 분석 결과: {analysis_result}")
        
        # JSON 파싱 시도
        import json
        try:
            parsed_result = json.loads(analysis_result)
            workflow_type = parsed_result.get("workflow_type", "full_pipeline")
            required_steps = parsed_result.get("required_steps", ["epic", "story", "point"])
        except json.JSONDecodeError:
            logger.warning("JSON 파싱 실패, 기본값 사용")
            # 간단한 키워드 기반 분석으로 폴백
            workflow_type, required_steps = _fallback_analysis(user_input)
            logger.info(f"폴백 분석 결과: {workflow_type}, {required_steps}")
        
        # 상태 업데이트
        updated_state = {
            **state,
            "workflow_type": workflow_type,
            "required_steps": required_steps,
            "current_step": "analyze",
            "completed_steps": ["analyze"],
            "execution_start_time": start_time,
            "step_times": {"analyze": (datetime.now() - start_time).total_seconds()},
            "next_action": "epic" if "epic" in required_steps else required_steps[0] if required_steps else "done"
        }
        
        logger.info(f"쿼리 분석 완료: {workflow_type}, 필요 단계: {required_steps}")
        return updated_state
        
    except Exception as e:
        logger.error(f"쿼리 분석 오류: {str(e)}")
        # 오류 발생 시 전체 파이프라인으로 처리
        return {
            **state,
            "workflow_type": "full_pipeline",
            "required_steps": ["epic", "story", "point"],
            "current_step": "analyze",
            "completed_steps": ["analyze"],
            "errors": state.get("errors", []) + [f"쿼리 분석 오류: {str(e)}"],
            "execution_start_time": start_time,
            "step_times": {"analyze": (datetime.now() - start_time).total_seconds()},
            "next_action": "epic"
        }


def _fallback_analysis(user_input: str) -> tuple[str, List[str]]:
    """LLM 분석 실패시 키워드 기반 폴백 분석"""
    user_input_lower = user_input.lower()
    
    # 에픽만
    if any(keyword in user_input_lower for keyword in ["에픽", "epic", "큰 기능", "프로젝트 분할"]):
        if not any(keyword in user_input_lower for keyword in ["스토리", "story", "포인트", "point"]):
            return "epic_only", ["epic"]
    
    # 스토리만
    if any(keyword in user_input_lower for keyword in ["스토리", "story", "상세 기능", "세부 기능"]):
        if not any(keyword in user_input_lower for keyword in ["에픽", "epic", "포인트", "point"]):
            return "story_only", ["story"]
    
    # 포인트만
    if any(keyword in user_input_lower for keyword in ["포인트", "point", "추정", "예측", "시간"]):
        if not any(keyword in user_input_lower for keyword in ["에픽", "epic", "스토리", "story"]):
            return "point_only", ["point"]
    
    # 기본적으로 전체 파이프라인
    return "full_pipeline", ["epic", "story", "point"]