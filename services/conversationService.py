from typing import AsyncGenerator
from database.database import SessionLocal
from database.tables.UseModel import UseModel
from database.tables.Conversation import Conversation
from database.tables.ConversationPost import ConversationPost
from config import secret
from openai import OpenAI
from sqlalchemy.orm import Session

def create_conversation(user_id:int) -> int:
    """
    新しい会話スレッドを開始します
    """
    with SessionLocal() as db:
        db_conversation = Conversation(user_id=user_id, model_name="")
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)

    return db_conversation.id

def post_message(prompt: str) -> AsyncGenerator[str, None]:
    """
    LLMにメッセージを送信します
    """
    
    with SessionLocal() as db:
        conversation_id = get_conversation_id(1, db)
        model = get_model(1, db)

        conversation = (
            db.query(ConversationPost)
            .filter(ConversationPost.conversation_id == conversation_id)
            .order_by(ConversationPost.posted_at.asc())
            .limit(10)
            .all()
        )
        
        messages = []
        for post in conversation:
            messages.append({"role": post.role, "content": post.message})

        return generate(model, conversation_id, messages, prompt, db)

openai = OpenAI(
    organization=secret['organization'],
    project=secret['project'],
    api_key=secret['api_key'],
)

def get_conversation_id(user_id: int, db: Session) -> int:
    """
    ユーザーIDから会話IDを取得する
    """
    conversation = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.id.desc())
        .first()
    )
    return conversation.id if conversation else None

def get_model(user_id: int, db: Session) -> str:
    """
    ユーザーIDからモデル名を取得する
    """
    use_model = (
        db.query(UseModel)
        .filter(UseModel.user_id == user_id)
        .first()
    )

    if not use_model:
        use_model = UseModel(user_id=user_id, model_for_text_generation="gpt-4o-mini")
        db.add(use_model)
        db.commit()
        db.refresh(use_model)
        return use_model.model_for_text_generation
    
    return use_model.model_for_text_generation

async def generate(model: str, conversation_id: int, messages: list, prompt: str, db: Session):
    """
    GPTモデルのストリーミング生成
    """
    messages.append({"role": "user", "content": prompt})
    stream = openai.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    content_full = ''
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content is None:
            continue
        content_full += content
        yield content

    user_post = ConversationPost(conversation_id=conversation_id, role="user", message=prompt)
    assistant_post = ConversationPost(conversation_id=conversation_id, role="assistant", message=content_full)
    db.add_all([user_post, assistant_post])
    db.commit()