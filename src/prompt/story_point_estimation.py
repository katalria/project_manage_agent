from langchain.prompts import PromptTemplate

story_point_estimation_prompt = PromptTemplate(
    input_variables=["story", "reference_stories"],
    template="""
당신은 숙련된 스크럼 마스터입니다.

다음 스토리의 스토리 포인트를 추정해야 합니다. 참고 스토리들을 기반으로 상대적 추정을 수행하세요.

### 스토리 포인트 추정 기준
- 1 포인트: 매우 간단한 작업 (1-2시간)
- 2 포인트: 간단한 작업 (반나절)  
- 3 포인트: 보통 작업 (1일)
- 5 포인트: 복잡한 작업 (2-3일)
- 8 포인트: 매우 복잡한 작업 (1주일)

### 추정할 스토리:
{story}

### 같은 영역(area)의 참고 스토리들:
{reference_stories}

### 추정 프로세스
1. **복잡도 분석**: 추정할 스토리의 기술적/비즈니스적 복잡도 평가
2. **참고 스토리 비교**: 같은 영역의 기존 스토리들과 상대적 비교
3. **위험도 고려**: 불확실성과 의존성 요소 반영
4. **최종 포인트 결정**: 1, 2, 3, 5, 8 중 선택

### 출력 포맷(JSON):
{{
  "estimated_point": 3,
  "reasoning": "상세한 추정 근거",
  "complexity_factors": [
    "기술적 복잡도 요소",
    "비즈니스 복잡도 요소"
  ],
  "similar_stories": [
    "유사한 참고 스토리 제목들"
  ],
  "confidence_level": "high/medium/low"
}}

### 중요사항
- 반드시 유효한 JSON 형식으로만 응답하세요
- JSON 외 다른 설명이나 주석은 포함하지 마세요
- estimated_point는 반드시 1, 2, 3, 5, 8 중 하나여야 합니다

결과:
"""
)