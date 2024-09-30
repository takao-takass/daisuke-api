import json
from openai import OpenAI

import os

print(os.getcwd())  # 現在の作業ディレクトリを表示

# secret.jsonを読み取る
with open('secret.json', encoding="utf-8") as f:
    secret = json.load(f)

# クライアントを作成
client = OpenAI(
  organization=secret['organization'],
  project=secret['project'],
  api_key=secret['api_key'],
)

RESPONSE = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {"role": "system", "content": "私はあなたのアシスタントです。"},
    {"role": "user", "content": "こんにちは！"},
  ]
)

print(RESPONSE)
