from langchain.prompts import PromptTemplate

epic_story_classification_prompt = PromptTemplate(
    input_variables=["tasks"],
    template="""
당신은 숙련된 프로젝트 매니저입니다.

다음은 전달받은 여러 개의 업무(Task)입니다. 이 Task들은 현재 에픽(Epic)인지 스토리(Story)인지 구분되지 않은 상태입니다. 당신의 역할은 이 Task들을 의미에 따라 적절히 **에픽과 그 하위 스토리로 분류 및 재구성**하는 것입니다.

### 업무 분류 기준
- **Epic**: 비즈니스 가치를 제공하는 큰 기능 단위 (보통 2-4주 소요)
  - 예: "사용자 인증 시스템", "상품 추천 엔진"
  - 여러 스프린트에 걸쳐 완성되는 기능
- **Story**: Epic 내에서 독립적으로 완료 가능한 최소 가치 단위 (1-3일 소요)
  - 예: "로그인 기능", "비밀번호 재설정"
  - 한 스프린트 내에서 완료 가능한 업무
- Story는 Epic 없이 존재하지 않으며, Epic은 하나 이상 Story로 구성되어야 함.

### 작성 규칙
- Epic은 하나 이상의 관련된 Task로부터 추출된 **기능 중심 제목**과 설명을 포함합니다.
- Story는 Epic 내에서 **사용자 중심 가치를 제공하는 세분화된 업무 단위**입니다.
- 각 Story는 'title', 'description', 'point', 'area' 항목을 포함합니다.
- Story 'title'은 사용자 가치 중심으로 작성하되, 다음 형식 중 적절한 것을 선택:
  - "As a [사용자], I want [기능] so that [목적]" (표준형)
  - "[사용자]가 [목적]을 위해 [기능]을 사용할 수 있다" (자연스러운 한글형)
- 'point'는 1, 2, 3, 5, 8 중 하나로 설정해야 하며, 그 이상의 업무량이 필요한 Task는 더 작은 여러 개의 Story로 나눠야 합니다.
- 결과는 반드시 아래 JSON 포맷을 따르세요.
- 한글로 작성해주세요.

### 분석 프로세스
1. **Task 분석**: 각 Task의 규모와 성격을 파악c
2. **그루핑**: 유사한 기능/목적의 Task들을 묶어 Epic 후보 식별
3. **Epic 구성**: 그룹별로 Epic 제목과 목표 설정
4. **Story 변환**: 각 Task를 사용자 중심 Story로 변환
5. **검증**: Epic-Story 관계와 포인트 추정 검토

### 특수 상황 처리
- 단일 Task가 Epic 수준인 경우: 더 작은 Story들로 분해
- Task가 너무 작아 Story가 되기 어려운 경우: 관련 Task들과 결합
- 기술적 Task(예: 환경 설정): "개발팀"을 사용자로 하여 Story화

### 품질 검증
결과 출력 전 다음을 확인하세요:
- 각 Epic이 명확한 비즈니스 목표를 가지는가?
- 각 Story가 독립적으로 완료 가능한가?
- Story 포인트가 8을 초과하지 않는가?
- 모든 Story가 실제 사용자 가치를 제공하는가?

### 입력 Task 목록:
{tasks}

### 출력 포맷(JSON):
[
  {{
    "epic": {{
      "title": "string",
      "description": "string", 
      "business_value": "string",
      "priority": "string"
    }},
    "stories": [
      {{
        "title": "string",
        "description": "string",
        "acceptance_criteria": ["string"],
        "point": 1,
        "area": "string",
        "dependencies": ["string"]
      }}
    ]
  }}
]

### 중요사항
- 반드시 유효한 JSON 형식으로만 응답하세요
- JSON 외 다른 설명이나 주석은 포함하지 마세요
- dependencies에서 참조하는 Story는 같은 Epic 내의 다른 Story title을 사용하세요
- 의존성이 없는 Story는 dependencies를 빈 배열 []로 설정하세요

결과:
"""
)