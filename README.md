# What is daisuke-api?

## Run local with container
```bash
docker run --env-file .env -p 8000:8000 takao0119/daisuke-api
```

## 概要
daisukeは、AIチャットアプリです。TAKAHIRO TADAによって実験的な機能が追加されることがあります。daisuke-apiは、daisukeのAPIサーバーを提供します。

## 技術スタック
- Python
- FastAPI
- OpenAPI
- SQL Alchemy
- Alembic

## Kubernetesマニフェスト
🔒Secret : https://github.com/takao-takass/daisuke-api-k8s

# データベースのマイグレーションコマンド

マイグレーションに追加
```bash
alembic revision --autogenerate -m "メッセージ"
```

マイグレーションを適用
```bash
alembic upgrade head
```

マイグレーションを巻き戻す
```bash
alembic downgrade -1
```