import pandas as pd
import json
from typing import Dict, List
from langchain_community.chat_models import ChatOpenAI
from story_point.prompts import story_point_estimation_prompt


class StoryPointAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.prompt = story_point_estimation_prompt
        self.reference_data = None
    
    def load_reference_csv(self, csv_path: str) -> bool:
        """CSV 파일에서 참고 스토리 데이터를 로드합니다."""
        try:
            self.reference_data = pd.read_csv(csv_path)
            print(f"Reference data loaded: {len(self.reference_data)} stories")
            return True
        except Exception as e:
            print(f"Failed to load CSV: {e}")
            return False
    
    def get_reference_stories_by_area(self, area: str) -> List[Dict]:
        """특정 영역의 참고 스토리들을 반환합니다."""
        if self.reference_data is None:
            return []
        
        area_stories = self.reference_data[
            self.reference_data['area'].str.lower() == area.lower()
        ]
        
        reference_stories = []
        for _, row in area_stories.iterrows():
            reference_stories.append({
                'title': row.get('title', ''),
                'description': row.get('description', ''),
                'point': row.get('point', 0),
                'area': row.get('area', '')
            })
        
        return reference_stories
    
    def estimate_story_point(self, story: Dict, area: str = None) -> Dict:
        """스토리 포인트를 추정합니다."""
        # area가 지정되지 않은 경우 스토리의 area 사용
        if area is None:
            area = story.get('area', '')
        
        # 참고 스토리들 가져오기
        reference_stories = self.get_reference_stories_by_area(area)
        
        # 참고 스토리가 없는 경우 기본 추정
        if not reference_stories:
            return {
                "estimated_point": 3,
                "reasoning": "참고할 수 있는 동일 영역의 스토리가 없어 기본값으로 추정했습니다.",
                "complexity_factors": ["참고 데이터 부족"],
                "similar_stories": [],
                "confidence_level": "low"
            }
        
        # 스토리 정보 포맷팅
        story_text = f"""
제목: {story.get('title', '')}
설명: {story.get('description', '')}
영역: {story.get('area', '')}
완료조건: {', '.join(story.get('acceptance_criteria', []))}
"""
        
        # 참고 스토리들 포맷팅
        reference_text = ""
        for ref in reference_stories:
            reference_text += f"""
- 제목: {ref['title']}
  설명: {ref['description']}
  포인트: {ref['point']}
  
"""
        
        # LLM에 질의
        formatted_prompt = self.prompt.format(
            story=story_text,
            reference_stories=reference_text
        )
        
        try:
            response = self.llm.predict(formatted_prompt)
            result = self.parse_estimation_response(response)
            print(f"Story point estimation: {result}")
            return result
        except Exception as e:
            print(f"Estimation failed: {e}")
            return {
                "estimated_point": 3,
                "reasoning": f"추정 중 오류 발생: {str(e)}",
                "complexity_factors": ["오류 발생"],
                "similar_stories": [],
                "confidence_level": "low"
            }
    
    def parse_estimation_response(self, response: str) -> Dict:
        """LLM 응답을 파싱합니다."""
        try:
            # JSON 응답에서 코드 블록 제거
            content = response.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            # JSON 파싱
            parsed_data = json.loads(content)
            
            # 유효성 검증
            valid_points = [1, 2, 3, 5, 8]
            if parsed_data.get('estimated_point') not in valid_points:
                parsed_data['estimated_point'] = 3
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Raw response: {response}")
            return {
                "estimated_point": 3,
                "reasoning": "응답 파싱 실패로 기본값 적용",
                "complexity_factors": ["파싱 오류"],
                "similar_stories": [],
                "confidence_level": "low"
            }
    
    def estimate_multiple_stories(self, stories: List[Dict]) -> List[Dict]:
        """여러 스토리의 포인트를 일괄 추정합니다."""
        results = []
        for story in stories:
            estimation = self.estimate_story_point(story)
            story_with_estimation = story.copy()
            story_with_estimation.update(estimation)
            results.append(story_with_estimation)
        
        return results