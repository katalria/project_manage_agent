from typing import Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

def user_input_node(state: Dict) -> Dict:
    """
    사용자 입력을 LangGraph 상태에 넣는 entry node.
    초기에 next_action을 "epic"으로 설정하여 분기하도록 함.
    """
    user_input = state.get("input")  # FastAPI나 CLI에서 전달될 입력
    messages = state.get("messages", [])
    
    if not user_input:
        raise ValueError("사용자 입력이 없습니다. 'input' 필드에 문자열을 넣어주세요.")

    # 메시지 추가
    messages = add_messages(messages, [HumanMessage(content=user_input)])

    return {
        "input": user_input,
        "messages": messages,
        "next_action": "epic"  # 초기 분기 대상 (나중에 LLM으로 판단 가능)
    }