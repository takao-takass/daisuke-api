import mariadb
from config import conn_params, secret
from openai import OpenAI

openai = OpenAI(
    organization=secret['organization'],
    project=secret['project'],
    api_key=secret['api_key'],
)

def get_conversation_id(user_id: int, cur: mariadb.Cursor) -> int:
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

    for (id,) in cur:
        return id

def get_model(user_id: int, cur: mariadb.Cursor) -> str:
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

    for (model_for_text_generation,) in cur:
        return model_for_text_generation

async def generate(model: str, conversation_id: int, messages: list, prompt: str):
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