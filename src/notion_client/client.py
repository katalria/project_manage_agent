import os
from typing import Dict, List, Any
from notion_client import Client
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class NotionService:
    """노션 API 서비스"""
    
    def __init__(self):
        self.client = Client(auth=os.environ.get("NOTION_TOKEN"))
        self.database_id = os.environ.get("NOTION_DATABASE_ID")
    
    def create_project_page(self, project_data: Dict[str, Any]) -> str:
        """프로젝트 페이지 생성"""
        try:
            # 프로젝트 메인 페이지 생성
            main_page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": f"프로젝트: {project_data.get('project_name', '새 프로젝트')}"
                                }
                            }
                        ]
                    },
                    "Status": {
                        "select": {
                            "name": "Planning"
                        }
                    },
                    "Type": {
                        "select": {
                            "name": "Project"
                        }
                    },
                    "Created": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    }
                }
            )
            
            page_id = main_page["id"]
            logger.info(f"Created project page: {page_id}")
            
            # 페이지 내용 추가
            self._add_project_content(page_id, project_data)
            
            return page_id
            
        except Exception as e:
            logger.error(f"Failed to create project page: {str(e)}")
            raise
    
    def _add_project_content(self, page_id: str, project_data: Dict[str, Any]):
        """프로젝트 페이지 내용 추가"""
        
        epic_results = project_data.get("epic_results", [])
        total_points = sum(
            sum(sp.estimated_point for sp in result["story_points"])
            for result in epic_results
        )
        
        # 페이지 블록 구성
        blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "프로젝트 개요"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"📊 총 {len(epic_results)}개 에픽, {project_data.get('total_stories', 0)}개 스토리, {total_points}개 스토리 포인트"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"🕒 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        }
                    ]
                }
            }
        ]
        
        # 에픽별로 내용 추가
        for i, epic_result in enumerate(epic_results, 1):
            epic = epic_result["epic"]
            stories = epic_result["stories"]
            story_points = epic_result["story_points"]
            
            # 에픽 헤더
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"📋 Epic {i}: {epic.title}"
                            }
                        }
                    ]
                }
            })
            
            # 에픽 설명
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": epic.description
                            }
                        }
                    ]
                }
            })
            
            # 에픽 정보
            blocks.extend([
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"💼 비즈니스 가치: {epic.business_value}"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"🔥 우선순위: {epic.priority}"
                                }
                            }
                        ]
                    }
                }
            ])
            
            # 수용 기준
            if epic.acceptance_criteria:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "✅ 수용 기준:"
                                },
                                "annotations": {
                                    "bold": True
                                }
                            }
                        ]
                    }
                })
                
                for criterion in epic.acceptance_criteria:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": criterion
                                    }
                                }
                            ]
                        }
                    })
            
            # 스토리 섹션
            if stories:
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"📝 Stories ({len(stories)}개)"
                                }
                            }
                        ]
                    }
                })
                
                for story in stories:
                    # 스토리 포인트 찾기
                    story_point = next(
                        (sp for sp in story_points if sp.story_title == story.title),
                        None
                    )
                    
                    point_text = f" - {story_point.estimated_point}pt" if story_point else ""
                    
                    blocks.append({
                        "object": "block",
                        "type": "toggle",
                        "toggle": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"{story.title}{point_text}"
                                    },
                                    "annotations": {
                                        "bold": True
                                    }
                                }
                            ],
                            "children": [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": story.description
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": f"🏷️ 도메인: {story.domain} | 타입: {story.story_type}"
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    })
            
            # 구분선
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        
        # 블록 추가 (API 제한으로 인해 100개씩 나누어 추가)
        chunk_size = 100
        for i in range(0, len(blocks), chunk_size):
            chunk = blocks[i:i + chunk_size]
            self.client.blocks.children.append(
                block_id=page_id,
                children=chunk
            )
    
    def get_page_url(self, page_id: str) -> str:
        """페이지 URL 생성"""
        # 노션 페이지 URL 형식: https://www.notion.so/{page_id}
        clean_page_id = page_id.replace("-", "")
        return f"https://www.notion.so/{clean_page_id}"


# 싱글톤 인스턴스
_notion_service = None


def get_notion_service() -> NotionService:
    """노션 서비스 싱글톤 인스턴스 반환"""
    global _notion_service
    if _notion_service is None:
        _notion_service = NotionService()
    return _notion_service