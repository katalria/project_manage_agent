import json
import logging
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from story_point.prompts import STORY_POINT_ESTIMATION_PROMPT
from story_point.models import StoryPointEstimation, StoryPointRequest, StoryPointProcessingStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoryPointEstimationAgent:
    """스토리 포인트 추정 agent"""
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o-mini", temperature: float = 0.2, csv_file_path: str = "data/reference_stories.csv"):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=openai_api_key
        )
        self.processing_tasks: Dict[str, StoryPointProcessingStatus] = {}
        self.csv_file_path = csv_file_path
        self.reference_data: Optional[pd.DataFrame] = None
        
        # CSV 파일 초기화
        self._initialize_csv_file()

    def _initialize_csv_file(self):
        """CSV 파일 초기화 - 파일이 없으면 생성"""
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(self.csv_file_path), exist_ok=True)
            
            if not os.path.exists(self.csv_file_path):
                # 기본 컬럼으로 빈 CSV 파일 생성
                columns = [
                    'story_title', 'description', 'domain', 'story_type', 'tags',
                    'acceptance_criteria', 'estimated_point', 'estimation_method',
                    'reasoning', 'complexity_factors', 'similar_stories',
                    'confidence_level', 'assumptions', 'risks', 
                    'epic_title', 'epic_description', 'epic_business_value',
                    'epic_priority', 'created_at'
                ]
                df = pd.DataFrame(columns=columns)
                df.to_csv(self.csv_file_path, index=False)
                logger.info(f"새로운 CSV 파일 생성: {self.csv_file_path}")
            
            # CSV 파일 로드
            self.load_reference_data()
            
        except Exception as e:
            logger.error(f"CSV 파일 초기화 실패: {str(e)}")

    def load_reference_data(self) -> bool:
        """CSV 파일에서 참고 스토리 데이터 로드"""
        try:
            if os.path.exists(self.csv_file_path):
                self.reference_data = pd.read_csv(self.csv_file_path)
                logger.info(f"참고 데이터 로드 완료: {len(self.reference_data)}개 스토리")
                return True
            else:
                logger.warning(f"CSV 파일을 찾을 수 없음: {self.csv_file_path}")
                return False
        except Exception as e:
            logger.error(f"CSV 파일 로드 실패: {str(e)}")
            return False

    def get_reference_stories_by_domain(self, domain: str, limit: int = 10) -> List[Dict]:
        """특정 도메인의 참고 스토리들을 반환"""
        if self.reference_data is None or self.reference_data.empty:
            return []
        
        try:
            # 도메인별 필터링
            domain_stories = self.reference_data[
                self.reference_data['domain'].str.lower() == domain.lower()
            ]
            
            # 최신순으로 정렬하고 제한
            domain_stories = domain_stories.sort_values('created_at', ascending=False).head(limit)
            
            reference_stories = []
            for _, row in domain_stories.iterrows():
                reference_stories.append({
                    'story_title': row.get('story_title', ''),
                    'description': row.get('description', ''),
                    'domain': row.get('domain', ''),
                    'estimated_point': row.get('estimated_point', 3),
                    'reasoning': row.get('reasoning', ''),
                    'complexity_factors': str(row.get('complexity_factors', '')),
                    'confidence_level': row.get('confidence_level', 'medium')
                })
            
            return reference_stories
            
        except Exception as e:
            logger.error(f"참고 스토리 조회 실패: {str(e)}")
            return []

    def save_estimation_to_csv(self, story_info, estimation: StoryPointEstimation, epic_info=None):
        """추정 결과를 CSV 파일에 저장"""
        try:
            # 새로운 데이터 행 생성
            new_data = {
                'story_title': estimation.story_title,
                'description': getattr(story_info, 'description', ''),
                'domain': estimation.domain,
                'story_type': getattr(story_info, 'story_type', ''),
                'tags': str(getattr(story_info, 'tags', [])),
                'acceptance_criteria': str(getattr(story_info, 'acceptance_criteria', [])),
                'estimated_point': estimation.estimated_point,
                'estimation_method': estimation.estimation_method,
                'reasoning': estimation.reasoning,
                'complexity_factors': str(estimation.complexity_factors),
                'similar_stories': str(estimation.similar_stories),
                'confidence_level': estimation.confidence_level,
                'assumptions': str(estimation.assumptions),
                'risks': str(estimation.risks),
                'epic_title': getattr(epic_info, 'title', '') if epic_info else '',
                'epic_description': getattr(epic_info, 'description', '') if epic_info else '',
                'epic_business_value': getattr(epic_info, 'business_value', '') if epic_info else '',
                'epic_priority': getattr(epic_info, 'priority', '') if epic_info else '',
                'created_at': datetime.now().isoformat()
            }
            
            # DataFrame에 추가
            new_row = pd.DataFrame([new_data])
            
            # CSV 파일에 추가 (헤더 없이)
            new_row.to_csv(self.csv_file_path, mode='a', header=False, index=False)
            
            # 메모리의 reference_data도 업데이트
            if self.reference_data is not None:
                self.reference_data = pd.concat([self.reference_data, new_row], ignore_index=True)
            else:
                self.reference_data = new_row
            
            logger.info(f"추정 결과를 CSV에 저장: {estimation.story_title}")
            
        except Exception as e:
            logger.error(f"CSV 저장 실패: {str(e)}")

    def _generate_estimations_with_llm(self, prompt: ChatPromptTemplate, user_input: str, epic_info: str, story_info: str, reference_stories: str) -> str:
        """LLM을 사용하여 스토리 포인트 추정"""
        try:
            logger.info("스토리 포인트 추정 시작")
            
            formatted_prompt = prompt.format(
                user_input=user_input,
                epic_info=epic_info,
                story_info=story_info,
                reference_stories=reference_stories
            )
            
            response = self.llm.invoke(formatted_prompt)
            logger.info("스토리 포인트 추정 완료")
            return response.content
            
        except Exception as e:
            logger.error(f"스토리 포인트 추정 중 오류: {str(e)}")
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

    def _validate_estimations(self, parsed_estimations: List[Dict]) -> List[StoryPointEstimation]:
        """스토리 포인트 추정 결과 검증 및 변환"""
        try:
            logger.info("스토리 포인트 추정 결과 검증 시작")
            
            validated_estimations = []
            for estimation_data in parsed_estimations:
                try:
                    # 필수 필드 확인 및 기본값 설정
                    story_title = estimation_data.get("story_title", "제목 없음")
                    estimated_point = estimation_data.get("estimated_point", 3)
                    domain = estimation_data.get("domain", "fullstack")
                    estimation_method = estimation_data.get("estimation_method", "cross_area")
                    reasoning = estimation_data.get("reasoning", "추정 근거 없음")
                    complexity_factors = estimation_data.get("complexity_factors", [])
                    similar_stories = estimation_data.get("similar_stories", [])
                    confidence_level = estimation_data.get("confidence_level", "medium")
                    assumptions = estimation_data.get("assumptions", [])
                    risks = estimation_data.get("risks", [])
                    
                    # 유효한 포인트 값 검증
                    valid_points = [1, 2, 3, 5, 8]
                    if estimated_point not in valid_points:
                        estimated_point = 3
                        
                    # 리스트 필드 검증
                    if isinstance(complexity_factors, str):
                        complexity_factors = [complexity_factors]
                    if isinstance(similar_stories, str):
                        similar_stories = [similar_stories]
                    if isinstance(assumptions, str):
                        assumptions = [assumptions]
                    if isinstance(risks, str):
                        risks = [risks]
                    
                    estimation = StoryPointEstimation(
                        story_title=story_title,
                        estimated_point=estimated_point,
                        domain=domain,
                        estimation_method=estimation_method,
                        reasoning=reasoning,
                        complexity_factors=complexity_factors,
                        similar_stories=similar_stories,
                        confidence_level=confidence_level,
                        assumptions=assumptions,
                        risks=risks
                    )
                    validated_estimations.append(estimation)
                    
                except Exception as e:
                    logger.warning(f"스토리 포인트 추정 결과 검증 실패: {str(e)}")
                    logger.warning(f"문제가 된 데이터: {estimation_data}")
                    continue
            
            logger.info(f"검증 완료: {len(validated_estimations)}개 추정 결과")
            return validated_estimations
            
        except Exception as e:
            logger.error(f"스토리 포인트 추정 결과 검증 중 오류: {str(e)}")
            raise e
    
    def _create_fallback_estimation(self, story_title: str = "기본 스토리") -> List[StoryPointEstimation]:
        """기본 스토리 포인트 추정 생성 (fallback)"""
        logger.info("기본 스토리 포인트 추정 생성")
        
        fallback_estimation = StoryPointEstimation(
            story_title=story_title,
            estimated_point=3,
            domain="fullstack",
            estimation_method="cross_area",
            reasoning="추정에 실패하여 기본값을 적용했습니다.",
            complexity_factors=["추정 실패"],
            similar_stories=[],
            confidence_level="low",
            assumptions=["기본값 적용"],
            risks=["추정 정확도 낮음"]
        )
        return [fallback_estimation]
        
    async def estimate_story_points(self, request: StoryPointRequest) -> List[StoryPointEstimation]:
        """스토리 포인트 추정 (동기)"""
        try:
            # 1. 참고 스토리 데이터 가져오기
            domain = getattr(request.story_info, 'domain', None) or 'fullstack'
            reference_stories = self.get_reference_stories_by_domain(domain)
            
            # 참고 스토리 문자열 생성
            reference_stories_str = ""
            if reference_stories:
                for ref in reference_stories:
                    reference_stories_str += f"""
                        - 제목: {ref['story_title']}
                        설명: {ref['description']}
                        도메인: {ref['domain']}
                        포인트: {ref['estimated_point']}
                        추정근거: {ref['reasoning']}
  
                    """
            else:
                reference_stories_str = "참고할 수 있는 동일 도메인의 스토리가 없습니다."
            
            # 2. LLM으로 스토리 포인트 추정
            raw_response = self._generate_estimations_with_llm(
                STORY_POINT_ESTIMATION_PROMPT,
                request.user_input,
                str(request.epic_info) if request.epic_info else "",
                str(request.story_info),
                reference_stories_str
            )
            
            # 3. 응답 파싱
            parsed_estimations = self._parse_response(raw_response)
            
            # 4. 추정 결과 검증 및 변환
            validated_estimations = self._validate_estimations(parsed_estimations)
            
            # 5. 결과가 없으면 기본 추정 생성
            if not validated_estimations:
                validated_estimations = self._create_fallback_estimation(request.story_info.title)
            
            # 6. 유효한 추정 결과만 CSV에 저장
            if validated_estimations and len(validated_estimations) > 0:
                for estimation in validated_estimations:
                    # fallback이 아닌 실제 추정 결과만 저장
                    if estimation.confidence_level != "low" or estimation.reasoning != "추정에 실패하여 기본값을 적용했습니다.":
                        self.save_estimation_to_csv(request.story_info, estimation, request.epic_info)
            
            return validated_estimations
            
        except Exception as e:
            logger.error(f"스토리 포인트 추정 중 오류: {str(e)}")
            # 오류 발생 시 기본 추정 반환
            return self._create_fallback_estimation(request.story_info.title if request.story_info else "기본 스토리")
        
    async def estimate_story_points_async(self, request: StoryPointRequest, task_id: str):
        """스토리 포인트 추정 (비동기)"""
        try:
            # 상태 업데이트
            self.processing_tasks[task_id] = StoryPointProcessingStatus(
                task_id=task_id,
                status="processing",
                message="스토리 포인트 추정 중..."
            )
            
            estimations = await self.estimate_story_points(request)
            
            # 완료 상태 업데이트
            self.processing_tasks[task_id] = StoryPointProcessingStatus(
                task_id=task_id,
                status="completed",
                message="스토리 포인트 추정 완료",
                result=estimations
            )
            
        except Exception as e:
            logger.error(f"비동기 스토리 포인트 추정 오류: {str(e)}")
            self.processing_tasks[task_id] = StoryPointProcessingStatus(
                task_id=task_id,
                status="failed",
                message="스토리 포인트 추정 실패",
                error=str(e)
            )
    
    def get_task_status(self, task_id: str) -> StoryPointProcessingStatus:
        """작업 상태 조회"""
        return self.processing_tasks.get(task_id)