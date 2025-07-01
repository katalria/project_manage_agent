from langchain.prompts import PromptTemplate

epic_prompt = PromptTemplate(
    input_variables=["tasks"],
    template="""
당신은 숙련된 프로젝트 매니저입니다.

다음은 전달받은 여러 개의 업무(Task)입니다. 이 Task들은 현재 에픽(Epic)인지 스토리(Story)인지 구분되지 않은 상태입니다. 당신의 역할은 이 Task들을 의미에 따라 적절히 **에픽과 그 하위 스토리로 분류 및 재구성**하는 것입니다.

### 업무 분류 기준
- Epic: 하나의 큰 기능 또는 사용자 목표. 이 안에 여러 Story가 포함됨.
- Story: Epic 안에서 사용자가 얻는 구체적인 가치 또는 세부 기능. 작은 단위의 업무.
- Story는 Epic 없이 존재하지 않으며, Epic은 하나 이상 Story로 구성되어야 함.

### 작성 규칙
- Epic은 하나 이상의 관련된 Task로부터 추출된 **기능 중심 제목**과 설명(goal)을 포함합니다.
- Story는 Epic 내에서 **사용자 중심 가치를 제공하는 세분화된 업무 단위**입니다.
- 각 Story는 'title', 'description', 'point', 'area' 항목을 포함합니다.
- 각 Story의 'title'은 **as a 사용자 유형, i want 어떤 기능(행위/목표) so that 어떤 이익(이유)**의 형식으로 작성합니다.
- 'point'는 1, 2, 3, 5, 8 중 하나로 설정해야 하며, 그 이상의 업무량이 필요한 Task는 더 작은 여러 개의 Story로 나눠야 합니다.
- 결과는 반드시 아래 JSON 포맷을 따르세요.
- 한글로 작성해주세요

### 입력 Task 목록:
{tasks}

### 출력 포맷(JSON):
[
  {{
    "epic": {{
      "title": string,
      "description": string,
      "goal": string,
      "stakeholders": [string, ...]
    }},
    "stories": [
      {{
        "title": string,
        "description": string,
        "point": int,
        "area": string
      }},
      ...
    ]
  }},
  ...
]

결과:
"""
)