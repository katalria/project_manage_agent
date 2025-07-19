import json
import logging
from typing import Dict, List

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from story.prompts import STORY_GENERATOR_PROMPT
from story.models import Story, StoryRequest, StoryProcessingStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoryGeneratorAgent:
    """스토리 생성 agent"""
    
    def __init__(self, openai_api_key: str,  model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=openai_api_key
        )
        self.processing_tasks: Dict[str, StoryProcessingStatus] = {}

    def _generate_storys_with_llm(self, prompt: ChatPromptTemplate, user_input: str, epic_info: str, max_storys: int) -> str:
        """LLM을 사용하여 스토리 생성"""
        try:
            logger.info("스토리 생성 시작")
            
            prompt = prompt.format(
                user_input=user_input,
                epic_info=epic_info,
                max_storys=max_storys
            )
            
            response = self.llm.invoke(prompt)
            logger.info("스토리 생성 완료")
            return response.content
            
        except Exception as e:
            logger.error(f"스토리 생성 중 오류: {str(e)}")
            raise e

    def _parse_response(self, raw_response: str) -> List[Dict]:
        """응답 파싱"""
        try:
            logger.info("응답 파싱 시작")
            
            # JSON 파싱 시도
            try:
                parsed_data = json.loads(raw_response)
                return parsed_data
            except json.JSONDecodeError:
                # JSON 추출 시도
                import re
                json_pattern = r'\[.*\]'
                match = re.search(json_pattern, raw_response, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    parsed_data = json.loads(json_str)
                    return parsed_data
                else:
                    logger.error(f"유효하지 않은 형태의 raw_response : {raw_response}")
                    raise ValueError("유효한 JSON을 찾을 수 없음")
            
        except Exception as e:
            logger.error(f"응답 파싱 중 오류: {str(e)}")
            raise e

### 추후 개선    
    # def _validate_storys(self, parsed_storys: List[Dict]) -> List[Story]:
    #     """스토리 검증 및 변환"""
    #     try:
    #         logger.info("에픽 검증 시작")
            
    #         validated_epics = []
    #         for story_data in parsed_storys:
    #             try:
    #                 # 직접 구조 처리 (중첩 구조 제거)
    #                 epic_info = epic_data
                    
    #                 # 필수 필드 확인 및 기본값 설정
    #                 title = epic_info.get("title", "제목 없음")
    #                 description = epic_info.get("description", "설명 없음")
    #                 business_value = epic_info.get("business_value", "비즈니스 가치 미정의")
    #                 priority = epic_info.get("priority", "Medium")
    #                 acceptance_criteria = epic_info.get("acceptance_criteria", [])
                    
                    

    #                 # 수락 기준이 문자열인 경우 리스트로 변환
    #                 if isinstance(acceptance_criteria, str):
    #                     acceptance_criteria = [acceptance_criteria]
                    
    #                 # 기본 수락 기준 추가 (비어있는 경우)
    #                 if not acceptance_criteria:
    #                     acceptance_criteria = [
    #                         f"{title} 기능이 정상적으로 동작한다",
    #                         "사용자 테스트를 통과한다",
    #                         "성능 요구사항을 만족한다"
    #                     ]
                    
    #                 epic = Story(
    #                     title=title,
    #                     description=description,
    #                     business_value=business_value,
    #                     priority=priority,
    #                     acceptance_criteria=acceptance_criteria,
    #                 )
    #                 validated_epics.append(epic)
                    
    #             except Exception as e:
    #                 logger.warning(f"에픽 검증 실패: {str(e)}")
    #                 logger.warning(f"문제가 된 데이터: {epic_data}")
    #                 continue
            
    #         logger.info(f"검증 완료: {len(validated_epics)}개 에픽")
    #         return validated_epics
            
    #     except Exception as e:
    #         logger.error(f"에픽 검증 중 오류: {str(e)}")
    #         raise e
    
    # def _create_fallback_epic(self, user_input: str) -> List[Epic]:
    #     """기본 에픽 생성 (fallback)"""
    #     logger.info("기본 에픽 생성")
        
    #     fallback_epic = Epic(
    #         title="기본 에픽",
    #         description=f"에픽 생성에 실패하여 기본 에픽을 생성했습니다. 사용자 요청: {user_input}",
    #         business_value="기본 비즈니스 가치",
    #         priority="Medium",
    #         acceptance_criteria=[
    #             "기본 기능이 정상적으로 동작한다",
    #             "사용자 요구사항을 만족한다",
    #             "테스트를 통과한다"
    #         ]
    #     )
    #     return [fallback_epic]
        
    async def generate_storys(self, request: StoryRequest) -> List[Story]:
        """에픽 생성 (동기)"""
        try:
            # 1. LLM으로 에픽 생성
            raw_response = self._generate_storys_with_llm(
                STORY_GENERATOR_PROMPT,
                request.user_input,
                request.epic_info,
                request.max_storys
            )
            

            # 2. 응답 파싱
            parsed_storys = self._parse_response(raw_response)
            
            # 3. 스토리 검증 및 변환
            # validated_storys = self._validate_storys(parsed_storys)
            
            # 4. 결과가 없으면 기본 스토리 생성
            # if not validated_storys:
            #     validated_storys = self._create_fallback_story(request.user_input)
            
            return parsed_storys
            
        except Exception as e:
            logger.error(f"스토리 생성 중 오류: {str(e)}")
            # 오류 발생 시 기본 스토리 반환
            return self._create_fallback_story(request.user_input)
        
    async def generate_storys_async(self, request: StoryRequest, task_id: str):
        """스토리 생성 (비동기)"""
        try:
            # 상태 업데이트
            self.processing_tasks[task_id] = StoryProcessingStatus(
                task_id=task_id,
                status="processing",
                message="스토리 생성 중..."
            )
            
            storys = await self.generate_storys(request)
            
            # 완료 상태 업데이트
            self.processing_tasks[task_id] = StoryProcessingStatus(
                task_id=task_id,
                status="completed",
                message="스토리 생성 완료",
                result=storys
            )
            
        except Exception as e:
            logger.error(f"비동기 스토리 생성 오류: {str(e)}")
            self.processing_tasks[task_id] = StoryProcessingStatus(
                task_id=task_id,
                status="failed",
                message="스토리 생성 실패",
                error=str(e)
            )
    
    def get_task_status(self, task_id: str) -> StoryProcessingStatus:
        """작업 상태 조회"""
        return self.processing_tasks.get(task_id)