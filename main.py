import json
from openai import OpenAI
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/chat/test")
def read_root():

    with open('secret.json', encoding="utf-8") as f:
        secret = json.load(f)

    # クライアントを作成
    client = OpenAI(
        organization=secret['organization'],
        project=secret['project'],
        api_key=secret['api_key'],
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say this is a test"}],
        stream=True,
    )

    return StreamingResponse(stream)

    #for chunk in stream:
    #    if chunk.choices[0].delta.content is not None:
    #        print(chunk.choices[0].delta.content, end="")
#
    #return {"Hello": "World"}

"""
with open('secret.json', encoding="utf-8") as f:
    secret = json.load(f)

# クライアントを作成
client = OpenAI(
    organization=secret['organization'],
    project=secret['project'],
    api_key=secret['api_key'],
)

stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say this is a test"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
"""
        
"""
RESPONSE = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "私はあなたのアシスタントです。"},
        {"role": "user", "content": "こんにちは！"},
    ]
)

print(RESPONSE)
"""