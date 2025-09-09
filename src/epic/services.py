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
            
            # 2. JSON 파싱하여 Epic 객체로 변환
            try:
                epic_data_list = json.loads(raw_response)
                epics = []
                
                for epic_data in epic_data_list:
                    epic = Epic(
                        title=epic_data.get('title', '제목 없음'),
                        description=epic_data.get('description', '설명 없음'),
                        business_value=epic_data.get('business_value', '비즈니스 가치 없음'),
                        priority=epic_data.get('priority', 'Medium'),
                        acceptance_criteria=epic_data.get('acceptance_criteria', []),
                        included_tasks=epic_data.get('included_tasks', [])
                    )
                    epics.append(epic)
                
                logger.info(f"에픽 파싱 완료: {len(epics)}개")
                return epics
                
            except json.JSONDecodeError as je:
                logger.error(f"JSON 파싱 오류: {str(je)}")
                logger.error(f"원본 응답: {raw_response}")
                # 파싱 실패시 기본 에픽 반환
                return [Epic(
                    title="기본 에픽",
                    description=f"JSON 파싱에 실패하여 기본 에픽을 생성했습니다. 사용자 요청: {request.user_input}",
                    business_value="기본 비즈니스 가치",
                    priority="Medium",
                    acceptance_criteria=["기본 기능이 정상적으로 동작한다"],
                    included_tasks=["기본 작업"]
                )]
            
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
            
            # 2. JSON 파싱하여 Epic 객체로 변환
            try:
                epic_data_list = json.loads(raw_response)
                epics = []
                
                for epic_data in epic_data_list:
                    epic = Epic(
                        title=epic_data.get('title', '제목 없음'),
                        description=epic_data.get('description', '설명 없음'),
                        business_value=epic_data.get('business_value', '비즈니스 가치 없음'),
                        priority=epic_data.get('priority', 'Medium'),
                        acceptance_criteria=epic_data.get('acceptance_criteria', []),
                        included_tasks=epic_data.get('included_tasks', [])
                    )
                    epics.append(epic)
                
                logger.info(f"task-to-epic 파싱 완료: {len(epics)}개")
                return epics
                
            except json.JSONDecodeError as je:
                logger.error(f"JSON 파싱 오류: {str(je)}")
                logger.error(f"원본 응답: {raw_response}")
                # 파싱 실패시 기본 에픽 반환
                return [Epic(
                    title="기본 에픽 (Task 변환)",
                    description=f"JSON 파싱에 실패하여 기본 에픽을 생성했습니다. 사용자 요청: {request.user_input}",
                    business_value="기본 비즈니스 가치",
                    priority="Medium",
                    acceptance_criteria=["기본 기능이 정상적으로 동작한다"],
                    included_tasks=["기본 작업"]
                )]
            
        except Exception as e:
            logger.error(f"에픽 생성 중 오류: {str(e)}")
            # 오류 발생 시 기본 에픽 반환
            raise
