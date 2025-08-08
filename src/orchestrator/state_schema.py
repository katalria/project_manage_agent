# orchestrator/state_schema.py
from typing import TypedDict, Literal


class AgentState(TypedDict, total=False):
    input: str
    epics: list[str]
    stories: list[str]
    points: list[int]
    next_action: Literal["epic", "story", "point", "question", "done"]
