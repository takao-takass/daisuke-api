from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from models.GptRequest import GptRequest
from services.conversationService import create_conversation, post_message

router = APIRouter()

@router.put("/conversation")
async def create():
    """
    新しい会話を始めるためのエンドポイント
    """
    return {"conversation_id": create_conversation(1)}

@router.post("/conversation/message")
async def post(gpt_request: GptRequest):
    """
    会話でメッセージを送信するためのエンドポイント（HTTP/1.1専用 チャンク送信）
    """
    return StreamingResponse(post_message(gpt_request.prompt),media_type="text/plain")

@router.post("/conversation/messageStream")
async def post_stream(gpt_request: GptRequest):
    """
    会話でメッセージを送信するためのエンドポイント（HTTP/1.1、HTTP/2両対応 SSE送信）
    """
    return EventSourceResponse(post_message(gpt_request.prompt))