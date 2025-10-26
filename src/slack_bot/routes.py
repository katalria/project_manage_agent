from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse
from utils.logger import get_logger
from .bot import handler

router = APIRouter(prefix="/slack", tags=["Slack"])
logger = get_logger(__name__)

@router.get("/events")
async def slack_events_verification(challenge: str = Query(None)):
    """슬랙 URL 검증 - challenge 파라미터 응답"""
    logger.info(f"Slack URL verification requested with challenge: {challenge}")
    
    if challenge:
        # 슬랙 URL 검증을 위해 challenge 값을 그대로 반환
        return PlainTextResponse(content=challenge)
    
    return {"status": "Slack events endpoint is ready"}

@router.post("/events")
async def slack_events(request: Request):
    """슬랙 이벤트 핸들러"""
    logger.info("Slack event received")
    return await handler.handle(request)

@router.get("/interactive")
async def slack_interactive_verification():
    """슬랙 인터랙티브 URL 검증"""
    logger.info("Slack interactive URL verification")
    return {"status": "Slack interactive endpoint is ready"}

@router.post("/interactive")
async def slack_interactive(request: Request):
    """슬랙 인터랙티브 핸들러"""
    logger.info("Slack interactive request received")
    return await handler.handle(request)

@router.get("/commands")
async def slack_commands_verification():
    """슬랙 명령어 URL 검증"""
    logger.info("Slack commands URL verification")
    return {"status": "Slack commands endpoint is ready"}

@router.post("/commands")
async def slack_commands(request: Request):
    """슬랙 슬래시 커맨드 핸들러"""
    logger.info("Slack command received")
    return await handler.handle(request)