from fastapi import APIRouter, Request
from .bot import handler

router = APIRouter(prefix="/slack", tags=["Slack"])

@router.post("/events")
async def slack_events(request: Request):
    """슬랙 이벤트 핸들러"""
    return await handler.handle(request)

@router.post("/interactive")
async def slack_interactive(request: Request):
    """슬랙 인터랙티브 핸들러"""
    return await handler.handle(request)

@router.post("/commands")
async def slack_commands(request: Request):
    """슬랙 슬래시 커맨드 핸들러"""
    return await handler.handle(request)