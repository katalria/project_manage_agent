import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from main import app
from project.models import EpicStoryGroup, Epic, Story



@pytest.fixture
def client():
    return TestClient(app)




# TaskClassificationService tests removed as this service doesn't exist in the new structure


class TestFastAPIEndpoints:
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Project Management Agent API"}
    
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_classify_tasks_endpoint_success(self, client):
        payload = {
            "tasks": ["로그인 기능 개발", "회원가입 페이지 만들기"]
        }
        
        response = client.post("/classify-tasks", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert len(data["result"]) == 1
        assert "epic" in data["result"][0]
        assert "stories" in data["result"][0]
    
    def test_classify_tasks_endpoint_empty_tasks(self, client):
        payload = {"tasks": []}
        
        response = client.post("/classify-tasks", json=payload)
        
        assert response.status_code == 200
    
    def test_classify_tasks_endpoint_invalid_payload(self, client):
        payload = {"invalid_field": ["task1"]}
        
        response = client.post("/classify-tasks", json=payload)
        
        assert response.status_code == 422
    
    def test_classify_tasks_endpoint_missing_tasks(self, client):
        payload = {}
        
        response = client.post("/classify-tasks", json=payload)
        
        assert response.status_code == 422


class TestResponseModels:
    
    def test_epic_story_group_validation(self):
        epic = Epic(
            title="사용자 인증 시스템",
            description="사용자가 안전하게 로그인하고 계정을 관리할 수 있는 시스템",
            goal="보안성과 사용성을 갖춘 인증 시스템 구축",
            stakeholders=["개발팀", "보안팀", "사용자"]
        )
        stories = [
            Story(
                title="로그인 기능 구현",
                description="이메일과 비밀번호로 로그인할 수 있는 기능",
                point=5,
                area="백엔드"
            )
        ]
        epic_story_group = EpicStoryGroup(epic=epic, stories=stories)
        
        assert epic_story_group.epic.title == "사용자 인증 시스템"
        assert len(epic_story_group.stories) == 1
        assert all(isinstance(story, Story) for story in epic_story_group.stories)
    
    def test_story_point_validation(self):
        with pytest.raises(ValueError):
            Story(
                title="Invalid Story",
                description="Story with invalid point",
                point=10,  # Invalid: should be 1-8
                area="백엔드"
            )
    
    def test_epic_required_fields(self):
        with pytest.raises(ValueError):
            Epic(
                title="Test Epic",
                # Missing required fields
            )


if __name__ == "__main__":
    pytest.main([__file__])