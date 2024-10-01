from asyncio import sleep
import json
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

class GptRequest(BaseModel):
    """
    GPTに質問するためのリクエストボディ
    """
    prompt: str

class DalleRequest(BaseModel):
    """
    DALL-Eで画像生成するためのリクエストボディ
    """
    prompt: str

@app.get("/")
def read_root():
    """
    DAISUKEはここにいるよ！
    """
    return "DAISUKE is here!"

@app.post("/test/gpt")
def test_gpt(gpt_request: GptRequest):
    """
    GPTモデルのテスト用エンドポイント
    """

    with open('secret.json', encoding="utf-8") as f:
        secret = json.load(f)

    openai = OpenAI(
        organization=secret['organization'],
        project=secret['project'],
        api_key=secret['api_key'],
    )

    def generate():
        stream = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": gpt_request.prompt}
            ],
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/test/reasoning")
def test_reasoning():
    """
    推論モデルのテスト用エンドポイント
    """

    with open('secret.json', encoding="utf-8") as f:
        secret = json.load(f)

    openai = OpenAI(
        organization=secret['organization'],
        project=secret['project'],
        api_key=secret['api_key'],
    )

    response = openai.chat.completions.create(
        model="o1-preview",
        messages=[
            {
                "role": "user", 
                "content": "'[1,2],[3,4],[5,6]' 形式の文字列として表される行列を受け取り、同じ形式で転置結果を出力する bash スクリプトを作成します。"
            }
        ]
    )

    return response.choices[0].message.content

@app.post("/test/image")
def test_image(dalle_request: DalleRequest):
    """
    画像生成のテスト用エンドポイント
    """

    with open('secret.json', encoding="utf-8") as f:
        secret = json.load(f)

    openai = OpenAI(
        organization=secret['organization'],
        project=secret['project'],
        api_key=secret['api_key'],
    )

    response = openai.images.generate(
        model="dall-e-3",
        prompt=dalle_request.prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return response.data[0].url


@app.post("/test/sse")
async def test_server_send_event():
    """
    Server-Sent Eventsのテスト用エンドポイント
    """

    async def waypoints_generator():
        waypoints = open('waypoints.json', encoding="utf-8")
        waypoints = json.load(waypoints)
        for waypoint in waypoints[0: 10]:
            data = json.dumps(waypoint)
            yield f"event: locationUpdate\ndata: {data}\n\n"
            await sleep(1)

    return StreamingResponse(waypoints_generator(), media_type="text/event-stream")

@app.post("/test/sse_gpt")
async def test_server_send_event_gpt(gpt_request: GptRequest):
    """
    GPTの回答をServer-Sent Eventsでストリーミングするテスト用エンドポイント
    """

    with open('secret.json', encoding="utf-8") as f:
        secret = json.load(f)

    openai = OpenAI(
        organization=secret['organization'],
        project=secret['project'],
        api_key=secret['api_key'],
    )

    async def generate():
        stream = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": gpt_request.prompt}
            ],
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    return EventSourceResponse(generate())
