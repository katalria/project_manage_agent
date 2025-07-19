from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


# 간단하고 명확한 Epic/Story 분류 프롬프트
EPIC_GENERATOR_PROMPT = ChatPromptTemplate.from_messages(
    [SystemMessagePromptTemplate.from_template(
        """
        [Role] 너는 숙련된 프로젝트 매니저다.
        [Goal] 2주 단위 스프린트를 기반으로 한 애자일 방법론에서, 프로젝트 정보에 따라 실제로 필요한 Epic을 도출하고 업무 계획을 수립하는 데 도움을 주는 것.
        [Instruction] 주어진 프로젝트 정보를 기반으로, 프로젝트를 구성하는 하나 이상의 Epic을 생성하라.
        [Constraints]
          - 출력은 반드시 [Output Format]을 따라야 한다.
          - Epic은 하나 이상의 스프린트에 걸쳐 진행되는 큰 기능 단위여야 한다.
          - 불필요한 설명, 주석, 마크다운 없이 JSON만 출력한다.
          - 최대 {max_epics}개의 Epic을 생성한다.
          - acceptance_criteria는 구체적으고 측정 가능한 기준으로 작성한다.
          - 개발자의 업무 영역만 작성한다.
        [Output Format]
        [
          {{
            "title": "에픽 제목",
            "description": "에픽 설명", 
            "business_value": "비즈니스 가치",
            "priority": "High|Medium|Low",
            "acceptance_criteria": ["수락 기준 1", "수락 기준 2", "수락 기준 3"]
          }},
        ]
        """
    ),
    HumanMessagePromptTemplate.from_template(
        """
        [Input] {user_input}
        [Context] {project_info}
        """
    )
    ]
)

TASK_TO_EPIC_CONVERTER_PROMPT = ChatPromptTemplate.from_messages(
    [SystemMessagePromptTemplate.from_template(
        """
        [Role] 너는 숙련된 프로젝트 매니저이자 업무 분석 전문가다.
        [Goal] 정리되지 않은 업무 리스트를 분석하여 관련 업무들을 그룹핑하고, 각 그룹을 하나의 Epic으로 변환하는 것.
        [Instruction] 
          1. 주어진 업무 리스트를 분석하여 기능적으로 관련된 업무들을 식별한다.
          2. 유사하거나 같은 기능 영역의 업무들을 하나의 Epic으로 그룹핑한다.
          3. 각 Epic에 포함되지 않은 개별 업무는 별도의 Epic으로 생성한다.
          4. Epic 제목은 해당 기능 영역을 대표하는 명확한 이름으로 작성한다.
        [Constraints]
          - 출력은 반드시 [Output Format]을 따라야 한다.
          - Epic은 하나 이상의 스프린트에 걸쳐 진행되는 큰 기능 단위여야 한다.
          - 불필요한 설명, 주석, 마크다운 없이 JSON만 출력한다.
          - 최대 {max_epics}개의 Epic을 생성한다.
          - 각 업무들로 에픽을 구성할 때 최소한의 에픽으로 구성한다
          - acceptance_criteria는 그룹핑된 업무들을 기반으로 구체적이고 측정 가능한 기준으로 작성한다.
          - 개발자의 업무 영역만 작성한다.
          - 각 Epic의 included_tasks에는 해당 Epic에 포함된 원본 업무들을 나열한다.
        [Output Format]
        [
          {{
            "title": "에픽 제목",
            "description": "에픽 설명", 
            "business_value": "비즈니스 가치",
            "priority": "High|Medium|Low",
            "acceptance_criteria": ["수락 기준 1", "수락 기준 2", "수락 기준 3"],
            "included_tasks": ["포함된 원본 업무 1", "포함된 원본 업무 2"],
          }}
        ]
        """
    ),

    HumanMessagePromptTemplate.from_template(
        """
        [Input] 정리되지 않은 업무 리스트:
        {user_input}
        
        [Context] {project_info}
        """
    )
    ]
)