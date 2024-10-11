import os
import json
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import mariadb

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000" 
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
    "db_port": 3306,
    "db_name": "chat"
}

secret['organization'] = os.getenv('ORGANIZATION', secret['organization'])
secret['project'] = os.getenv('PROJECT', secret['project'])
secret['api_key'] = os.getenv('API_KEY', secret['api_key'])
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

@app.put("/conversation")
def create_conversation():
    """
    新しい会話を始めるためのエンドポイント
    """
    with mariadb.connect(**conn_params) as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (user_id) 
                VALUES(?);
                """,
                (user_id,))

            cur.execute('COMMIT')

            conversation_id = get_conversation_id(user_id, cur)

            return {"conversation_id": conversation_id}

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

            return StreamingResponse(
                generate("gpt-4o-mini", conversation_id, messages, gpt_request.prompt),
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

            return EventSourceResponse(generate("gpt-4o-mini", conversation_id, messages, gpt_request.prompt))

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
