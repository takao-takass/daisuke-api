from asyncio import sleep
import json
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import mariadb

app = FastAPI()

user_id = 1

with open('secret.json', encoding="utf-8") as f:
    secret = json.load(f)

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
    with mariadb.connect(
        user=secret['db_user'],
        password=secret['db_password'],
        host=secret['db_host'],
        port=secret['db_port'],
        database=secret['db_name']
    ) as conn:

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

    with mariadb.connect(
        user=secret['db_user'],
        password=secret['db_password'],
        host=secret['db_host'],
        port=secret['db_port'],
        database=secret['db_name']
    ) as conn:

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

    with mariadb.connect(
        user=secret['db_user'],
        password=secret['db_password'],
        host=secret['db_host'],
        port=secret['db_port'],
        database=secret['db_name']
    ) as conn:

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


# @app.get("/")
# def read_root():
#     """
#     DAISUKEはここにいるよ！
#     """
#     return "DAISUKE is here!"
# 
# @app.post("/test/gpt")
# def test_gpt(gpt_request: GptRequest):
#     """
#     GPTモデルのテスト用エンドポイント
#     """
# 
#     with open('secret.json', encoding="utf-8") as f:
#         secret = json.load(f)
# 
#     openai = OpenAI(
#         organization=secret['organization'],
#         project=secret['project'],
#         api_key=secret['api_key'],
#     )
# 
#     def generate():
#         stream = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "user", "content": gpt_request.prompt}
#             ],
#             stream=True,
#         )
# 
#         content_full = ''
#         for chunk in stream:
#             content = chunk.choices[0].delta.content
#             if content is None:
#                 continue
#             content_full += content
#             yield content
# 
#         with mariadb.connect(
#             user=secret['db_user'],
#             password=secret['db_password'],
#             host=secret['db_host'],
#             port=secret['db_port'],
#             database=secret['db_name']
#         ) as conn:
# 
#             with conn.cursor() as cur:
#                 conversation_id = 1
#                 cur.execute(
#                     """
#                     INSERT INTO conversation_posts (conversation_id, `role`, message) 
#                     VALUES(?, 'User', ?);
#                     """,
#                     (conversation_id, gpt_request.prompt))
#                 cur.execute(
#                     """
#                     INSERT INTO conversation_posts (conversation_id, `role`, message) 
#                     VALUES(?, 'Assistant', ?);
#                     """,
#                     (conversation_id, content_full))
# 
#                 cur.execute('COMMIT')
# 
#     return StreamingResponse(generate(), media_type="text/plain")
# 
# 
# @app.post("/test/reasoning")
# def test_reasoning():
#     """
#     推論モデルのテスト用エンドポイント
#     """
# 
#     with open('secret.json', encoding="utf-8") as f:
#         secret = json.load(f)
# 
#     openai = OpenAI(
#         organization=secret['organization'],
#         project=secret['project'],
#         api_key=secret['api_key'],
#     )
# 
#     response = openai.chat.completions.create(
#         model="o1-preview",
#         messages=[
#             {
#                 "role": "user", 
#                 "content": "'[1,2],[3,4],[5,6]' 形式の文字列として表される行列を受け取り、同じ形式で転置結果を出力する bash スクリプトを作成します。"
#             }
#         ]
#     )
# 
#     return response.choices[0].message.content
# 
# @app.post("/test/image")
# def test_image(dalle_request: DalleRequest):
#     """
#     画像生成のテスト用エンドポイント
#     """
# 
#     with open('secret.json', encoding="utf-8") as f:
#         secret = json.load(f)
# 
#     openai = OpenAI(
#         organization=secret['organization'],
#         project=secret['project'],
#         api_key=secret['api_key'],
#     )
# 
#     response = openai.images.generate(
#         model="dall-e-3",
#         prompt=dalle_request.prompt,
#         size="1024x1024",
#         quality="standard",
#         n=1,
#     )
# 
#     return response.data[0].url
# 
# 
# @app.post("/test/sse")
# async def test_server_send_event():
#     """
#     Server-Sent Eventsのテスト用エンドポイント
#     """
# 
#     async def waypoints_generator():
#         waypoints = open('waypoints.json', encoding="utf-8")
#         waypoints = json.load(waypoints)
#         for waypoint in waypoints[0: 10]:
#             data = json.dumps(waypoint)
#             yield f"event: locationUpdate\ndata: {data}\n\n"
#             await sleep(1)
# 
#     return StreamingResponse(waypoints_generator(), media_type="text/event-stream")
# 
# @app.post("/test/sse_gpt")
# async def test_server_send_event_gpt(gpt_request: GptRequest):
#     """
#     GPTの回答をServer-Sent Eventsでストリーミングするテスト用エンドポイント
#     """
# 
#     with open('secret.json', encoding="utf-8") as f:
#         secret = json.load(f)
# 
#     openai = OpenAI(
#         organization=secret['organization'],
#         project=secret['project'],
#         api_key=secret['api_key'],
#     )
# 
#     async def generate():
#         stream = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "user", "content": gpt_request.prompt}
#             ],
#             stream=True,
#         )
# 
#         content_full = ''
#         for chunk in stream:
#             content = chunk.choices[0].delta.content
#             if content is None:
#                 continue
#             content_full += content
#             yield content
# 
#         with mariadb.connect(
#             user=secret['db_user'],
#             password=secret['db_password'],
#             host=secret['db_host'],
#             port=secret['db_port'],
#             database=secret['db_name']
#         ) as conn:
# 
#             with conn.cursor() as cur:
#                 conversation_id = 1
#                 cur.execute(
#                     """
#                     INSERT INTO conversation_posts (conversation_id, `role`, message) 
#                     VALUES(?, 'User', ?);
#                     """,
#                     (conversation_id, gpt_request.prompt))
#                 cur.execute(
#                     """
#                     INSERT INTO conversation_posts (conversation_id, `role`, message) 
#                     VALUES(?, 'Assistant', ?);
#                     """,
#                     (conversation_id, content_full))
# 
#                 cur.execute('COMMIT')
# 
#     return EventSourceResponse(generate())
# 
# 
# @app.post("/test/mariadb")
# async def test_mariadb():
#     """
#     Maria DBのテスト用エンドポイント
#     """
#     with open('secret.json', encoding="utf-8") as f:
#         secret = json.load(f)
# 
#     with mariadb.connect(
#         user=secret['db_user'],
#         password=secret['db_password'],
#         host=secret['db_host'],
#         port=secret['db_port'],
#         database=secret['db_name']
#     ) as conn:
# 
#         with conn.cursor() as cur:
# 
#             conversation_id = 1
#             cur.execute(
#                 """
#                 INSERT INTO conversation_posts (conversation_id, `role`, message) 
#                 VALUES(?, 'User', 'こんにちは。');
#                 """,
#                 (conversation_id))
# 
#             cur.execute('COMMIT')
# 
#             cur.execute(
#                 """
#                 SELECT role, message 
#                 FROM conversation_posts
#                 WHERE conversation_id = ?
#                 ORDER BY posted_at
#                 """ ,
#                 (conversation_id,))
# 
#             result = ""
#             for (role, message) in cur:
#                 result += f"{role}: {message}\n"
# 
#     return result
# 