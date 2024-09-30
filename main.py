import json
from openai import OpenAI
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/")
def read_root():
    return "DAISUKE is here!"

@app.post("/chat/test")
def read_root():

    with open('secret.json', encoding="utf-8") as f:
        secret = json.load(f)

    # クライアントを作成
    client = OpenAI(
        organization=secret['organization'],
        project=secret['project'],
        api_key=secret['api_key'],
    )

    def generate():
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "C#でfizz buzzを作ってください"}
            ],
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    return StreamingResponse(generate(), media_type="text/plain")
