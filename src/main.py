from fastapi import FastAPI, HTTPException
import json
import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

from routes import epic_detection_route
from models.models import TaskListInput, TaskClassificationResponse, EpicStoryGroup
from prompt.task2epic_story import epic_story_classification_prompt

load_dotenv()

app = FastAPI(
    title="Project Management Agent API",
    description="AI Agent for classifying tasks into epics and stories",
    version="0.1.0"
)

app.include_router(epic_detection_route.router, prefix="/epic_detection")

class OpenAITaskClassificationService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
        self.prompt = epic_story_classification_prompt
    
    async def classify_tasks(self, tasks: List[str]) -> List[EpicStoryGroup]:
        try:
            tasks_text = "\n".join([f"- {task}" for task in tasks])
            prompt_text = self.prompt.format(tasks=tasks_text)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 숙련된 프로젝트 매니저입니다. 응답은 반드시 유효한 JSON 형식으로만 제공해주세요."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 응답 파싱
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            result_data = json.loads(content)
            
            epic_story_groups = []
            for item in result_data:
                epic_story_groups.append(EpicStoryGroup(**item))
            
            return epic_story_groups
            
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"JSON parsing failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI task classification failed: {str(e)}")


# OpenAI 서비스는 API 키가 있을 때만 초기화
openai_service = None
try:
    openai_service = OpenAITaskClassificationService()
except ValueError as e:
    print(f"OpenAI service not available: {e}")


@app.get("/")
async def root():
    return {"message": "Project Management Agent API"}


@app.post("/classify-tasks-openai", response_model=TaskClassificationResponse)
async def classify_tasks_openai(request: TaskListInput):
    """
    업무 목록을 에픽과 스토리로 분류합니다. (OpenAI GPT-4o-mini 사용)
    """
    if openai_service is None:
        raise HTTPException(status_code=503, detail="OpenAI service is not available. Please check OPENAI_API_KEY environment variable.")
    
    epic_story_groups = await openai_service.classify_tasks(request.tasks)
    return TaskClassificationResponse(result=epic_story_groups)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)