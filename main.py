import json
from openai import OpenAI
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/")
def read_root():
    """
    DAISUKEはここにいるよ！
    """
    return "DAISUKE is here!"

@app.post("/test/gpt")
def test_gpt():
    """
    GPTモデルのテスト用エンドポイント
    """

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


@app.post("/test/reasoning")
def test_reasoning():
    """
    推論モデルのテスト用エンドポイント
    """

    with open('secret.json', encoding="utf-8") as f:
        secret = json.load(f)

    # クライアントを作成
    client = OpenAI(
        organization=secret['organization'],
        project=secret['project'],
        api_key=secret['api_key'],
    )

    response = client.chat.completions.create(
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
def test_image():
    """
    画像生成のテスト用エンドポイント
    """

    with open('secret.json', encoding="utf-8") as f:
        secret = json.load(f)

    client = OpenAI(
        organization=secret['organization'],
        project=secret['project'],
        api_key=secret['api_key'],
    )

    response = client.images.generate(
        model="dall-e-3",
        prompt="a white siamese cat",
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return response.data[0].url
