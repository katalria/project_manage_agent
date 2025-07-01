from langchain.chat_models import ChatOpenAI
from src.prompt.epic_detection_prompt import epic_prompt
from typing import List, Dict

class EpicDetectionAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.prompt = epic_prompt

    def extract_epics(self, tasks: List[str]) -> Dict:
        print(f"{tasks} tasks")
        joined_tasks = "\n".join(f"- {task}" for task in tasks)
        print(f"{joined_tasks} joined_tasks")
        formatted_prompt = self.prompt.format(tasks=joined_tasks)
        print(f"Formatted prompt: {formatted_prompt}")
        response = self.llm.predict(formatted_prompt)
        print(f"LLM response: {response}")
        result = self.parse_response(response)
        print(f"Parsed result: {result}")
        return result

    def parse_response(self, response: str) -> Dict:
        import json
        try:
            # JSON 응답에서 코드 블록 제거
            content = response.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            # JSON 파싱
            parsed_data = json.loads(content)
            
            # 기존 형식으로 변환
            result = {"epics": []}
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    epic_data = {
                        "title": item.get("epic", {}).get("title", ""),
                        "description": item.get("epic", {}).get("description", ""),
                        "goal": item.get("epic", {}).get("goal", ""),
                        "stakeholders": item.get("epic", {}).get("stakeholders", []),
                        "stories": []
                    }
                    
                    for story in item.get("stories", []):
                        epic_data["stories"].append({
                            "title": story.get("title", ""),
                            "description": story.get("description", ""),
                            "point": story.get("point", 0),
                            "area": story.get("area", "")
                        })
                    
                    result["epics"].append(epic_data)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Raw response: {response}")
            return {"epics": []}
