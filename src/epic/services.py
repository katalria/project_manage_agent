import json
import logging
from typing import List

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from epic.prompts import EPIC_GENERATOR_PROMPT, TASK_TO_EPIC_CONVERTER_PROMPT
from epic.models import Epic, EpicRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EpicGeneratorAgent:
    """에픽 생성 서비스 - LangChain Agent 형태"""

    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=openai_api_key
        )
    
    def _generate_epics_with_llm(self, prompt: ChatPromptTemplate, user_input: str, project_info: str, max_epics: int) -> str:
        """LLM을 사용하여 에픽 생성"""
        try:
            logger.info("에픽 생성 시작")
            
            prompt = prompt.format(
                user_input=user_input,
                project_info=project_info,
                max_epics=max_epics
            )
            
            response = self.llm.invoke(prompt)
            logger.info("에픽 생성 완료")
            return response.content
            
        except Exception as e:
            logger.error(f"에픽 생성 중 오류: {str(e)}")
            raise e
        
    def generate_epics(self, request: EpicRequest) -> List[Epic]:
        """에픽 생성 (동기)"""
        try:
            # 1. LLM으로 에픽 생성
            raw_response = self._generate_epics_with_llm(
                EPIC_GENERATOR_PROMPT,
                request.user_input,
                request.project_info,
                request.max_epics
            )
            
            return raw_response
            
        except Exception as e:
            logger.error(f"에픽 생성 중 오류: {str(e)}")
            # 오류 발생 시 기본 에픽 반환
            raise
        

    def convert_tasks_to_epics(self, request: EpicRequest) -> List[Epic]:
        """task to epic (동기)"""
        try:
            # 1. LLM으로 에픽 생성
            raw_response = self._generate_epics_with_llm(
                TASK_TO_EPIC_CONVERTER_PROMPT,
                request.user_input,
                request.project_info,
                request.max_epics
            )
            logger.info(f"생성 response: {raw_response}")
            
            return raw_response
            
        except Exception as e:
            logger.error(f"에픽 생성 중 오류: {str(e)}")
            # 오류 발생 시 기본 에픽 반환
            raise
