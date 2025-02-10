from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import mariadb
from config import conn_params, secret
from database.database import SessionLocal, Conversation
from models import GptRequest
from utils import get_conversation_id, get_model, generate

router = APIRouter()

@router.put("/conversation")
def create_conversation():
    """
    新しい会話を始めるためのエンドポイント
    """
    try:
        db = SessionLocal()
        db_conversation = Conversation(user_id=1, model_name="")
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
    finally:
        db.close()

    return {"conversation_id": db_conversation.id}

@router.post("/conversation/message")
def post_message(gpt_request: GptRequest):
    """
    会話でメッセージを送信するためのエンドポイント
    """
    with mariadb.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            conversation_id = get_conversation_id(1, cur)
            cur.execute(
                """
                SELECT `role` , message 
                FROM conversation_posts
                WHERE conversation_id = ?
                ORDER BY posted_at;
                """,
                (conversation_id,))

            messages = []
            for (role, message) in cur:
                messages.append({"role": role, "content": message})

            model = get_model(1, cur)

            return StreamingResponse(
                generate(model, conversation_id, messages, gpt_request.prompt),
                media_type="text/plain")

@router.post("/conversation/messageStream")
def post_message_stream(gpt_request: GptRequest):
    """
    会話でメッセージを送信するためのエンドポイント
    """
    with mariadb.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            conversation_id = get_conversation_id(1, cur)
            cur.execute(
                """
                SELECT `role` , message 
                FROM conversation_posts
                WHERE conversation_id = ?
                ORDER BY posted_at;
                """,
                (conversation_id,))

            messages = []
            for (role, message) in cur:
                messages.append({"role": role, "content": message})

            model = get_model(1, cur)

            return EventSourceResponse(generate(model, conversation_id, messages, gpt_request.prompt))