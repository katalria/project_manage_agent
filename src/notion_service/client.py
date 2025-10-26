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

        # 노션 데이터베이스 속성 매핑
        self.property_mapping = {
            "담당자": "people",
            "약칭/코드명": "rich_text",
            "타입": "select",
            "상태": "status",
            "스플린트 ID": "multi_select",
            "티켓 ID": "rich_text",
            "비고": "rich_text",
            "SP": "number",
            "날짜": "date",
            "최종 편집 일시": "last_edited_time",
            "최종 편집자": "last_edited_by",
            "대분류": "rich_text",
            "소분류": "rich_text",
            "우선순위": "select",
            "중분류": "rich_text"
        }
    
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
                    "상태": {
                        "status": {
                            "name": "Planning"
                        }
                    },
                    "타입": {
                        "select": {
                            "name": "Project"
                        }
                    },
                    "날짜": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    },
                    "대분류": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "프로젝트"
                                }
                            }
                        ]
                    },
                    "우선순위": {
                        "select": {
                            "name": "Medium"
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
        
        # 중복 제거를 위해 유니크한 스토리 포인트만 계산
        all_unique_story_points = set()
        for result in epic_results:
            for sp in result["story_points"]:
                all_unique_story_points.add((sp.story_title, sp.estimated_point))
        
        total_points = sum(point for _, point in all_unique_story_points)
        
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
                
                # 중복 방지를 위해 이미 처리된 스토리 추적
                processed_stories = set()
                
                for story in stories:
                    # 중복 스토리 건너뛰기
                    if story.title in processed_stories:
                        continue
                    processed_stories.add(story.title)
                    
                    # 스토리 포인트 찾기 (첫 번째 매칭만)
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
    
    def create_epic_page(self, epic_data: Dict[str, Any]) -> str:
        """에픽 페이지 생성"""
        try:
            epic_page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": epic_data.get('title', '새 에픽')
                                }
                            }
                        ]
                    },
                    "상태": {
                        "status": {
                            "name": "To Do"
                        }
                    },
                    "타입": {
                        "select": {
                            "name": "Epic"
                        }
                    },
                    "대분류": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "Epic"
                                }
                            }
                        ]
                    },
                    "우선순위": {
                        "select": {
                            "name": epic_data.get('priority', 'Medium')
                        }
                    },
                    "비고": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": epic_data.get('business_value', '')
                                }
                            }
                        ]
                    },
                    "날짜": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    }
                }
            )

            page_id = epic_page["id"]
            logger.info(f"Created epic page: {page_id}")

            # 에픽 상세 내용 추가
            self._add_epic_content(page_id, epic_data)

            return page_id

        except Exception as e:
            logger.error(f"Failed to create epic page: {str(e)}")
            raise

    def create_story_page(self, story_data: Dict[str, Any]) -> str:
        """스토리 페이지 생성"""
        try:
            # 스토리 포인트 정보
            story_point = story_data.get('story_point', {})
            estimated_point = story_point.get('estimated_point', 0) if story_point else 0

            story_page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": story_data.get('title', '새 스토리')
                                }
                            }
                        ]
                    },
                    "상태": {
                        "status": {
                            "name": "To Do"
                        }
                    },
                    "타입": {
                        "select": {
                            "name": "Story"
                        }
                    },
                    "대분류": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "Story"
                                }
                            }
                        ]
                    },
                    "중분류": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": story_data.get('domain', '')
                                }
                            }
                        ]
                    },
                    "소분류": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": story_data.get('story_type', '')
                                }
                            }
                        ]
                    },
                    "SP": {
                        "number": estimated_point
                    },
                    "티켓 ID": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"STORY-{story_data.get('id', '')}"
                                }
                            }
                        ]
                    },
                    "날짜": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    }
                }
            )

            page_id = story_page["id"]
            logger.info(f"Created story page: {page_id}")

            # 스토리 상세 내용 추가
            self._add_story_content(page_id, story_data)

            return page_id

        except Exception as e:
            logger.error(f"Failed to create story page: {str(e)}")
            raise

    def _add_epic_content(self, page_id: str, epic_data: Dict[str, Any]):
        """에픽 페이지 내용 추가"""
        blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Epic 설명"
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
                                "content": epic_data.get('description', '')
                            }
                        }
                    ]
                }
            }
        ]

        # 수용 기준 추가
        if epic_data.get('acceptance_criteria'):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "수용 기준"
                            }
                        }
                    ]
                }
            })

            for criterion in epic_data['acceptance_criteria']:
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

        self.client.blocks.children.append(
            block_id=page_id,
            children=blocks
        )

    def _add_story_content(self, page_id: str, story_data: Dict[str, Any]):
        """스토리 페이지 내용 추가"""
        blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Story 설명"
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
                                "content": story_data.get('description', '')
                            }
                        }
                    ]
                }
            }
        ]

        # 수용 기준 추가
        if story_data.get('acceptance_criteria'):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "수용 기준"
                            }
                        }
                    ]
                }
            })

            for criterion in story_data['acceptance_criteria']:
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

        # 스토리 포인트 정보 추가
        story_point = story_data.get('story_point')
        if story_point:
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "스토리 포인트 정보"
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
                                    "content": f"추정 포인트: {story_point.get('estimated_point', 0)}"
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
                                    "content": f"추정 방법: {story_point.get('estimation_method', '')}"
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
                                    "content": f"추정 근거: {story_point.get('reasoning', '')}"
                                }
                            }
                        ]
                    }
                }
            ])

        self.client.blocks.children.append(
            block_id=page_id,
            children=blocks
        )

    def create_step_by_step_pages(self, workflow_data: Dict[str, Any], step: str) -> List[str]:
        """단계별로 노션 페이지 생성"""
        page_ids = []

        try:
            if step == "epic" and workflow_data.get("epics"):
                # 에픽 페이지들 생성
                for epic in workflow_data["epics"]:
                    epic_data = {
                        "title": getattr(epic, 'title', ''),
                        "description": getattr(epic, 'description', ''),
                        "business_value": getattr(epic, 'business_value', ''),
                        "priority": getattr(epic, 'priority', 'Medium'),
                        "acceptance_criteria": getattr(epic, 'acceptance_criteria', [])
                    }
                    page_id = self.create_epic_page(epic_data)
                    page_ids.append(page_id)

            elif step == "story" and workflow_data.get("stories"):
                # 스토리 페이지들 생성
                for story in workflow_data["stories"]:
                    story_data = {
                        "title": getattr(story, 'title', ''),
                        "description": getattr(story, 'description', ''),
                        "domain": getattr(story, 'domain', ''),
                        "story_type": getattr(story, 'story_type', ''),
                        "acceptance_criteria": getattr(story, 'acceptance_criteria', []),
                        "id": getattr(story, 'id', '')
                    }
                    page_id = self.create_story_page(story_data)
                    page_ids.append(page_id)

            elif step == "point" and workflow_data.get("story_points"):
                # 스토리 포인트가 추가된 스토리 페이지들 업데이트
                stories = workflow_data.get("stories", [])
                story_points = workflow_data.get("story_points", [])

                # 스토리와 스토리 포인트 매핑
                for story in stories:
                    # 해당 스토리의 포인트 찾기
                    story_point = next(
                        (sp for sp in story_points if sp.story_title == story.title),
                        None
                    )

                    story_data = {
                        "title": getattr(story, 'title', ''),
                        "description": getattr(story, 'description', ''),
                        "domain": getattr(story, 'domain', ''),
                        "story_type": getattr(story, 'story_type', ''),
                        "acceptance_criteria": getattr(story, 'acceptance_criteria', []),
                        "id": getattr(story, 'id', ''),
                        "story_point": {
                            "estimated_point": getattr(story_point, 'estimated_point', 0),
                            "estimation_method": getattr(story_point, 'estimation_method', ''),
                            "reasoning": getattr(story_point, 'reasoning', '')
                        } if story_point else None
                    }

                    page_id = self.create_story_page(story_data)
                    page_ids.append(page_id)

            logger.info(f"단계별 페이지 생성 완료: {step}, 생성된 페이지 수: {len(page_ids)}")
            return page_ids

        except Exception as e:
            logger.error(f"단계별 페이지 생성 오류: {str(e)}")
            raise

    def update_workflow_progress(self, project_page_id: str, completed_steps: List[str],
                               step_results: Dict[str, Any]) -> None:
        """워크플로우 진행 상황을 프로젝트 페이지에 업데이트"""
        try:
            # 진행 상황 블록 추가
            progress_blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "🔄 워크플로우 진행 상황"
                                }
                            }
                        ]
                    }
                }
            ]

            # 단계별 상태 표시
            all_steps = ["epic", "story", "point"]
            for step in all_steps:
                status_emoji = "✅" if step in completed_steps else "⏳"
                step_name = {
                    "epic": "에픽 생성",
                    "story": "스토리 생성",
                    "point": "스토리 포인트 추정"
                }.get(step, step)

                progress_blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"{status_emoji} {step_name}"
                                }
                            }
                        ]
                    }
                })

            # 결과 요약
            if step_results:
                progress_blocks.extend([
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"📊 현재까지 결과: 에픽 {step_results.get('total_epics', 0)}개, 스토리 {step_results.get('total_stories', 0)}개, 총 SP {step_results.get('total_story_points', 0)}개"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "divider",
                        "divider": {}
                    }
                ])

            # 블록 추가
            self.client.blocks.children.append(
                block_id=project_page_id,
                children=progress_blocks
            )

            logger.info(f"워크플로우 진행 상황 업데이트 완료: {project_page_id}")

        except Exception as e:
            logger.error(f"워크플로우 진행 상황 업데이트 오류: {str(e)}")
            raise

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