from pydantic import BaseModel

class GptRequest(BaseModel):
    """
    GPTに質問するためのリクエストボディ
    """
    prompt: str