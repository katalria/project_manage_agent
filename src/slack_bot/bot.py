import os
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from dotenv import load_dotenv

from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# Slack 앱 초기화
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

# 메시지 핸들러
@app.message("hello")
def message_hello(message, say):
    """Hello 메시지 응답"""
    say(f"Hi <@{message['user']}>! 프로젝트 관리 봇입니다. `/project` 명령어로 시작해보세요!")

# 슬래시 커맨드 핸들러
@app.command("/project")
def handle_project_command(ack, body, client):
    """프로젝트 관리 슬래시 커맨드"""
    ack()
    
    user_id = body["user_id"]
    channel_id = body["channel_id"]
    
    # 초기 메뉴 블록
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🚀 *프로젝트 관리 AI Agent*\n\n어떤 작업을 도와드릴까요?"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 새 프로젝트 생성"
                    },
                    "action_id": "create_project",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📝 에픽/스토리 생성"
                    },
                    "action_id": "create_epic_story"
                }
            ]
        }
    ]
    
    client.chat_postMessage(
        channel=channel_id,
        blocks=blocks,
        text="프로젝트 관리 메뉴"
    )

# 버튼 클릭 핸들러
@app.action("create_epic_story")
def handle_create_epic_story(ack, body, client):
    """에픽/스토리 생성 버튼 클릭"""
    ack()
    
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    
    # 모달 열기
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "project_input_modal",
            "title": {"type": "plain_text", "text": "프로젝트 요구사항"},
            "submit": {"type": "plain_text", "text": "분석 시작"},
            "close": {"type": "plain_text", "text": "취소"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "project_description",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "description_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "프로젝트 요구사항을 자세히 설명해주세요...\n예: 사용자 인증 시스템을 만들어야 합니다. 로그인, 회원가입, 권한 관리가 필요합니다."}
                    },
                    "label": {"type": "plain_text", "text": "프로젝트 설명"}
                },
                {
                    "type": "input",
                    "block_id": "project_info",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "info_input",
                        "placeholder": {"type": "plain_text", "text": "웹 애플리케이션, 모바일 앱 등"}
                    },
                    "label": {"type": "plain_text", "text": "프로젝트 유형 (선택사항)"},
                    "optional": True
                }
            ]
        }
    )

# 모달 제출 핸들러
@app.view("project_input_modal")
def handle_project_submission(ack, body, client, view):
    """프로젝트 입력 모달 제출"""
    ack()
    
    user_id = body["user"]["id"]
    
    # 입력값 추출
    description = view["state"]["values"]["project_description"]["description_input"]["value"]
    project_info = view["state"]["values"]["project_info"]["info_input"]["value"] or ""
    
    logger.info(f"Project analysis request from {user_id}: {description}")
    
    # 채널에 분석 시작 메시지 전송
    client.chat_postMessage(
        channel=user_id,  # DM으로 전송
        text="🔄 프로젝트 분석을 시작합니다...",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔄 *프로젝트 분석 시작*\n\n**요구사항:**\n{description}\n\n**프로젝트 유형:** {project_info or '미지정'}\n\n분석 중입니다. 잠시만 기다려주세요..."
                }
            }
        ]
    )
    
    # 오케스트레이터 호출
    try:
        from orchestrator.orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        result = orchestrator.execute(
            user_input=description,
            project_info=project_info
        )
        
        if result["status"] == "completed":
            # 분석 결과를 사용자 세션에 저장 (실제로는 Redis나 DB를 사용해야 함)
            # 지금은 간단히 메모리에 저장
            if not hasattr(app, "user_sessions"):
                app.user_sessions = {}
            app.user_sessions[user_id] = result
            
            client.chat_postMessage(
                channel=user_id,
                text="✅ 분석이 완료되었습니다!",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *분석 완료*\n\n📊 **결과 요약:**\n• 에픽: {result['total_epics']}개\n• 스토리: {result['total_stories']}개\n• 스토리 포인트: {result['total_story_points']}개\n• 실행 시간: {result['execution_time']:.1f}초\n\n다음 단계를 선택해주세요:"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "📋 에픽 확인하기"
                                },
                                "action_id": "show_epics",
                                "style": "primary"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "📝 스토리 확인하기"
                                },
                                "action_id": "show_stories"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "🔢 포인트 확인하기"
                                },
                                "action_id": "show_points"
                            }
                        ]
                    }
                ]
            )
        else:
            client.chat_postMessage(
                channel=user_id,
                text="❌ 분석 중 오류가 발생했습니다.",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"❌ *분석 실패*\n\n**오류:** {', '.join(result.get('errors', ['알 수 없는 오류']))}\n\n다시 시도해주세요."
                        }
                    }
                ]
            )
    except Exception as e:
        logger.error(f"Orchestrator execution error: {str(e)}")
        client.chat_postMessage(
            channel=user_id,
            text=f"❌ 시스템 오류가 발생했습니다: {str(e)}"
        )

# 에픽 결과 보기
@app.action("show_epics")
def handle_show_epics(ack, body, client):
    """에픽 결과 표시"""
    ack()
    
    user_id = body["user"]["id"]
    
    # 사용자 세션에서 결과 가져오기
    if not hasattr(app, "user_sessions") or user_id not in app.user_sessions:
        client.chat_postMessage(
            channel=user_id,
            text="❌ 분석 결과를 찾을 수 없습니다. 다시 분석을 시작해주세요."
        )
        return
    
    result = app.user_sessions[user_id]
    epic_results = result.get("epic_results", [])
    
    if not epic_results:
        client.chat_postMessage(
            channel=user_id,
            text="📋 생성된 에픽이 없습니다."
        )
        return
    
    # 에픽들을 블록으로 구성
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📋 *생성된 에픽 ({len(epic_results)}개)*"
            }
        }
    ]
    
    for i, epic_result in enumerate(epic_results, 1):
        epic = epic_result["epic"]
        
        epic_text = f"*{i}. {epic.title}*\n"
        epic_text += f"📝 {epic.description}\n"
        epic_text += f"💼 비즈니스 가치: {epic.business_value}\n"
        epic_text += f"🔥 우선순위: {epic.priority}\n"
        
        if epic.acceptance_criteria:
            epic_text += f"✅ 수용 기준:\n"
            for criterion in epic.acceptance_criteria[:3]:  # 최대 3개만 표시
                epic_text += f"  • {criterion}\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": epic_text
            }
        })
        
        # 구분선 추가 (마지막 에픽 제외)
        if i < len(epic_results):
            blocks.append({"type": "divider"})
    
    # 액션 버튼 추가
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "📝 스토리 확인하기"
                },
                "action_id": "show_stories"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "✅ 승인 후 노션에 저장"
                },
                "action_id": "approve_and_save",
                "style": "primary"
            }
        ]
    })
    
    client.chat_postMessage(
        channel=user_id,
        blocks=blocks,
        text=f"생성된 에픽 {len(epic_results)}개"
    )

# 스토리 결과 보기
@app.action("show_stories")
def handle_show_stories(ack, body, client):
    """스토리 결과 표시"""
    ack()
    
    user_id = body["user"]["id"]
    
    if not hasattr(app, "user_sessions") or user_id not in app.user_sessions:
        client.chat_postMessage(
            channel=user_id,
            text="❌ 분석 결과를 찾을 수 없습니다. 다시 분석을 시작해주세요."
        )
        return
    
    result = app.user_sessions[user_id]
    epic_results = result.get("epic_results", [])
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📝 *생성된 스토리 ({result.get('total_stories', 0)}개)*"
            }
        }
    ]
    
    for epic_result in epic_results:
        epic = epic_result["epic"]
        stories = epic_result["stories"]
        
        if stories:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📋 {epic.title}*"
                }
            })
            
            for story in stories:
                story_text = f"• *{story.title}*\n"
                story_text += f"  📝 {story.description}\n"
                story_text += f"  🏷️ 도메인: {story.domain}\n"
                
                if story.acceptance_criteria:
                    story_text += f"  ✅ 수용기준:\n"
                    for criterion in story.acceptance_criteria[:2]:  # 최대 2개만 표시
                        story_text += f"    - {criterion}\n"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": story_text
                    }
                })
            
            blocks.append({"type": "divider"})
    
    # 액션 버튼 추가
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "🔢 포인트 확인하기"
                },
                "action_id": "show_points"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "✅ 승인 후 노션에 저장"
                },
                "action_id": "approve_and_save",
                "style": "primary"
            }
        ]
    })
    
    client.chat_postMessage(
        channel=user_id,
        blocks=blocks,
        text=f"생성된 스토리 {result.get('total_stories', 0)}개"
    )

# 스토리 포인트 결과 보기
@app.action("show_points")
def handle_show_points(ack, body, client):
    """스토리 포인트 결과 표시"""
    ack()
    
    user_id = body["user"]["id"]
    
    if not hasattr(app, "user_sessions") or user_id not in app.user_sessions:
        client.chat_postMessage(
            channel=user_id,
            text="❌ 분석 결과를 찾을 수 없습니다. 다시 분석을 시작해주세요."
        )
        return
    
    result = app.user_sessions[user_id]
    epic_results = result.get("epic_results", [])
    
    total_points = 0
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🔢 *스토리 포인트 추정 결과*"
            }
        }
    ]
    
    for epic_result in epic_results:
        epic = epic_result["epic"]
        story_points = epic_result["story_points"]
        
        if story_points:
            epic_points = sum(sp.estimated_point for sp in story_points)
            total_points += epic_points
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📋 {epic.title}* - 총 {epic_points} 포인트"
                }
            })
            
            for sp in story_points:
                point_text = f"• *{sp.story_title}*: {sp.estimated_point} 포인트\n"
                point_text += f"  📊 복잡도: {sp.complexity_factors}\n"
                point_text += f"  🎯 신뢰도: {sp.confidence_level}\n"
                point_text += f"  💭 추정 근거: {sp.reasoning[:100]}..."
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": point_text
                    }
                })
            
            blocks.append({"type": "divider"})
    
    # 총 포인트 요약
    blocks.insert(1, {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"📊 *전체 프로젝트 예상 포인트: {total_points} 포인트*"
        }
    })
    
    # 액션 버튼 추가
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "📋 에픽 다시 보기"
                },
                "action_id": "show_epics"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "✅ 승인 후 노션에 저장"
                },
                "action_id": "approve_and_save",
                "style": "primary"
            }
        ]
    })
    
    client.chat_postMessage(
        channel=user_id,
        blocks=blocks,
        text=f"스토리 포인트 추정 완료 - 총 {total_points} 포인트"
    )

# 노션에 저장하기
@app.action("approve_and_save")
def handle_approve_and_save(ack, body, client):
    """승인 후 노션에 저장"""
    ack()
    
    user_id = body["user"]["id"]
    
    if not hasattr(app, "user_sessions") or user_id not in app.user_sessions:
        client.chat_postMessage(
            channel=user_id,
            text="❌ 분석 결과를 찾을 수 없습니다. 다시 분석을 시작해주세요."
        )
        return
    
    result = app.user_sessions[user_id]
    
    # 노션 저장 진행 메시지
    client.chat_postMessage(
        channel=user_id,
        text="🔄 노션에 프로젝트 페이지를 생성하고 있습니다...",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🔄 *노션 페이지 생성 중*\n\n분석 결과를 노션에 저장하고 있습니다. 잠시만 기다려주세요..."
                }
            }
        ]
    )
    
    try:
        from notion_client.client import get_notion_service
        
        notion_service = get_notion_service()
        
        # 프로젝트 데이터 준비
        project_data = {
            "project_name": "AI 분석 프로젝트",
            "epic_results": result.get("epic_results", []),
            "total_stories": result.get("total_stories", 0),
            "total_story_points": result.get("total_story_points", 0),
            "execution_time": result.get("execution_time", 0)
        }
        
        # 노션 페이지 생성
        page_id = notion_service.create_project_page(project_data)
        page_url = notion_service.get_page_url(page_id)
        
        # 성공 메시지
        client.chat_postMessage(
            channel=user_id,
            text="✅ 노션 페이지가 성공적으로 생성되었습니다!",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *노션 페이지 생성 완료*\n\n프로젝트 분석 결과가 노션에 저장되었습니다!\n\n📊 **저장된 내용:**\n• 에픽: {result.get('total_epics', 0)}개\n• 스토리: {result.get('total_stories', 0)}개\n• 스토리 포인트: {result.get('total_story_points', 0)}개"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📄 노션 페이지 열기"
                            },
                            "url": page_url,
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🆕 새 프로젝트 시작"
                            },
                            "action_id": "create_epic_story"
                        }
                    ]
                }
            ]
        )
        
        logger.info(f"Successfully created Notion page {page_id} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to create Notion page: {str(e)}")
        client.chat_postMessage(
            channel=user_id,
            text="❌ 노션 페이지 생성 중 오류가 발생했습니다.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *노션 페이지 생성 실패*\n\n**오류:** {str(e)}\n\n환경 변수 설정을 확인해주세요:\n• `NOTION_TOKEN`: 노션 integration 토큰\n• `NOTION_DATABASE_ID`: 저장할 데이터베이스 ID"
                    }
                }
            ]
        )

# FastAPI 어댑터
handler = SlackRequestHandler(app)