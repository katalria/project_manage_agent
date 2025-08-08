from src.orchestrator.state_schema import AgentState


def manager_node(state: AgentState) -> AgentState:
    """
    현재 상태에 따라 어떤 agent를 실행할지 결정.
    """
    if "epics" not in state:
        return {**state, "next_action": "epic"}
    elif "stories" not in state:
        return {**state, "next_action": "story"}
    elif "points" not in state:
        return {**state, "next_action": "point"}
    else:
        return {**state, "next_action": "done"}
