from typing import List, Dict, Optional
from src.services.epic_detection_agent import EpicDetectionAgent
from src.services.story_point_agent import StoryPointAgent


class ProjectManagementOrchestrator:
    """
    Epic/Story 분류와 스토리 포인트 추정을 통합 관리하는 오케스트레이터
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4o-mini", 
                 temperature: float = 0.2,
                 reference_csv_path: Optional[str] = None):
        self.epic_agent = EpicDetectionAgent(model_name, temperature)
        self.point_agent = StoryPointAgent(model_name, temperature)
        
        # 참고 CSV 파일이 있다면 로드
        if reference_csv_path:
            self.load_reference_data(reference_csv_path)
    
    def load_reference_data(self, csv_path: str) -> bool:
        """참고 스토리 데이터를 로드합니다."""
        return self.point_agent.load_reference_csv(csv_path)
    
    def process_tasks_with_estimation(self, tasks: List[str], 
                                    estimate_points: bool = True) -> Dict:
        """
        태스크들을 Epic/Story로 분류하고 선택적으로 스토리 포인트를 추정합니다.
        
        Args:
            tasks: 분류할 태스크 목록
            estimate_points: 스토리 포인트 추정 여부
            
        Returns:
            Epic/Story 분류 결과와 포인트 추정 결과
        """
        print(f"Processing {len(tasks)} tasks...")
        
        # 1단계: Epic/Story 분류
        epic_result = self.epic_agent.extract_epics(tasks)
        print(f"Epic classification completed: {len(epic_result.get('epics', []))} epics")
        
        if not estimate_points:
            return epic_result
        
        # 2단계: 스토리 포인트 추정
        enhanced_result = {"epics": []}
        
        for epic_data in epic_result.get("epics", []):
            enhanced_epic = epic_data.copy()
            enhanced_stories = []
            
            for story in epic_data.get("stories", []):
                print(f"Estimating points for story: {story.get('title', 'Unknown')}")
                
                # 스토리 포인트 추정
                estimation = self.point_agent.estimate_story_point(story)
                
                # 원본 스토리에 추정 결과 추가
                enhanced_story = story.copy()
                enhanced_story.update({
                    "estimated_point": estimation["estimated_point"],
                    "estimation_reasoning": estimation["reasoning"],
                    "complexity_factors": estimation["complexity_factors"],
                    "similar_stories": estimation["similar_stories"],
                    "confidence_level": estimation["confidence_level"]
                })
                
                # 기존 point 필드를 estimated_point로 업데이트
                enhanced_story["point"] = estimation["estimated_point"]
                
                enhanced_stories.append(enhanced_story)
            
            enhanced_epic["stories"] = enhanced_stories
            enhanced_result["epics"].append(enhanced_epic)
        
        print("Story point estimation completed!")
        return enhanced_result
    
    def estimate_existing_stories(self, epic_story_data: Dict) -> Dict:
        """
        이미 분류된 Epic/Story 데이터에 대해 스토리 포인트만 추정합니다.
        
        Args:
            epic_story_data: 기존 Epic/Story 분류 데이터
            
        Returns:
            포인트 추정이 추가된 Epic/Story 데이터
        """
        enhanced_result = {"epics": []}
        
        for epic_data in epic_story_data.get("epics", []):
            enhanced_epic = epic_data.copy()
            enhanced_stories = []
            
            for story in epic_data.get("stories", []):
                estimation = self.point_agent.estimate_story_point(story)
                
                enhanced_story = story.copy()
                enhanced_story.update({
                    "estimated_point": estimation["estimated_point"],
                    "estimation_reasoning": estimation["reasoning"],
                    "complexity_factors": estimation["complexity_factors"],
                    "similar_stories": estimation["similar_stories"],
                    "confidence_level": estimation["confidence_level"]
                })
                
                enhanced_story["point"] = estimation["estimated_point"]
                enhanced_stories.append(enhanced_story)
            
            enhanced_epic["stories"] = enhanced_stories
            enhanced_result["epics"].append(enhanced_epic)
        
        return enhanced_result
    
    def get_estimation_summary(self, epic_story_data: Dict) -> Dict:
        """
        추정 결과에 대한 요약 정보를 제공합니다.
        """
        total_stories = 0
        total_points = 0
        area_summary = {}
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}
        
        for epic_data in epic_story_data.get("epics", []):
            epic_points = 0
            
            for story in epic_data.get("stories", []):
                total_stories += 1
                points = story.get("estimated_point", story.get("point", 0))
                total_points += points
                epic_points += points
                
                # 영역별 집계
                area = story.get("area", "Unknown")
                if area not in area_summary:
                    area_summary[area] = {"stories": 0, "points": 0}
                area_summary[area]["stories"] += 1
                area_summary[area]["points"] += points
                
                # 신뢰도 집계
                confidence = story.get("confidence_level", "medium")
                if confidence in confidence_distribution:
                    confidence_distribution[confidence] += 1
            
            epic_data["total_points"] = epic_points
        
        return {
            "total_epics": len(epic_story_data.get("epics", [])),
            "total_stories": total_stories,
            "total_story_points": total_points,
            "area_breakdown": area_summary,
            "confidence_distribution": confidence_distribution,
            "average_points_per_story": round(total_points / total_stories, 2) if total_stories > 0 else 0
        }