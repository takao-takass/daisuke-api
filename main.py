import os
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
import mariadb

class UseType(Enum):
    TEXT_GENERATION = 1

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.30:30003" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_id = 1

secret = {
    "organization": "org-xxxxxx",
    "project": "proj-xxxxxx",
    "api_key": "sk-xxxxxx",
    "db_user": "root",
    "db_host": "localhost",
    "db_password": "password",
    "db_port": "3306",
    "db_name": "chat"
}

secret['organization'] = os.getenv('OPENAI_ORGANIZATION', secret['organization'])
secret['project'] = os.getenv('OPENAI_PROJECT', secret['project'])
secret['api_key'] = os.getenv('OPENAI_API_KEY', secret['api_key'])
secret['db_user'] = os.getenv('DB_USER', secret['db_user'])
secret['db_host'] = os.getenv('DB_HOST', secret['db_host'])
secret['db_password'] = os.getenv('DB_PASSWORD', secret['db_password'])
secret['db_port'] = os.getenv('DB_PORT', secret['db_port'])
secret['db_name'] = os.getenv('DB_NAME', secret['db_name'])

conn_params = {
    "user": secret['db_user'],
    "password": secret['db_password'],
    "host": secret['db_host'],
    "port": int(secret['db_port']),
    "database": secret['db_name']
}

openai = OpenAI(
    organization=secret['organization'],
    project=secret['project'],
    api_key=secret['api_key'],
)

DATABASE_URL = f"mysql+pymysql://{conn_params['user']}:{conn_params['password']}@{conn_params['host']}/{conn_params['database']}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
Base = declarative_base()

class GptRequest(BaseModel):
    """
    GPTに質問するためのリクエストボディ
    """
    prompt: str

# class DalleRequest(BaseModel):
#     """
#     DALL-Eで画像生成するためのリクエストボディ
#     """
#     prompt: str

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    model_name = Column(String, index=False)

@app.put("/conversation")
def create_conversation():
    """
    新しい会話を始めるためのエンドポイント
    """
    try:
        db = SessionLocal()
        db_conversation = Conversation(user_id=user_id, model_name="")
        db.add(db_conversation)
        db.commit()
        #db.refresh(db_conversation)

    finally:
        db.close()

    return {"conversation_id": db_conversation.id}

@app.post("/conversation/message")
def post_message(gpt_request: GptRequest):
    """
    会話でメッセージを送信するためのエンドポイント
    """
    with mariadb.connect(**conn_params) as conn:

        with conn.cursor() as cur:
            conversation_id = get_conversation_id(user_id, cur)
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
                # Supported values are: 'system', 'assistant', 'user', 'function', and 'tool'.
                messages.append({"role": role, "content": message})

            model = get_model(user_id, UseType.TEXT_GENERATION, cur)

            return StreamingResponse(
                generate(model, conversation_id, messages, gpt_request.prompt),
                media_type="text/plain")


@app.post("/conversation/messageStream")
def post_message(gpt_request: GptRequest):
    """
    会話でメッセージを送信するためのエンドポイント
    """
    with mariadb.connect(**conn_params) as conn:

        with conn.cursor() as cur:
            conversation_id = get_conversation_id(user_id, cur)
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
                # Supported values are: 'system', 'assistant', 'user', 'function', and 'tool'.
                messages.append({"role": role, "content": message})
    
            model = get_model(user_id, UseType.TEXT_GENERATION, cur)

            return EventSourceResponse(generate(model, conversation_id, messages, gpt_request.prompt))

async def generate(model:str, conversation_id:int, messages:list, prompt:str):
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

    with mariadb.connect(**conn_params) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO conversation_posts (conversation_id, `role`, message) 
                VALUES(?, 'user', ?);
                """,
                (conversation_id, prompt))
            cur.execute(
                """
                INSERT INTO conversation_posts (conversation_id, `role`, message) 
                VALUES(?, 'assistant', ?);
                """,
                (conversation_id, content_full))
            cur.execute('COMMIT')


def get_conversation_id(user_id : int, cur : mariadb.Cursor) -> int:
    """
    ユーザーIDから会話IDを取得する
    """
    cur.execute(
        """
        SELECT MAX(id) as id
        FROM conversations
        WHERE user_id = ?;
        """,
        (user_id,))

    for (id) in cur:
        return id[0]

def get_model(user_id : int, use_type : UseType, cur : mariadb.Cursor) -> str:
    """
    ユーザーIDからモデル名を取得する
    """
    cur.execute(
        """
        SELECT model_for_text_generation
        FROM use_models
        WHERE user_id = ?;
        """,
        (user_id,))

    for (model_for_text_generation) in cur:
        if use_type == UseType.TEXT_GENERATION:
            return model_for_text_generation[0]

        return "gpt-4o-mini"
