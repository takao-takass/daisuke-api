"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app, get_conversation_id, generate

# test_main.py


client = TestClient(app)

@pytest.fixture
def mock_db():
    with patch('mariadb.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor

@pytest.fixture
def mock_openai():
    with patch('main.OpenAI') as mock_openai:
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.return_value = iter([MagicMock(choices=[MagicMock(delta=MagicMock(content="test response"))])])
        yield mock_instance

def test_create_conversation(mock_db):
    mock_db.fetchone.return_value = (1,)
    response = client.put("/conversation")
    assert response.status_code == 200
    assert response.json() == {"conversation_id": 1}
    mock_db.execute.assert_called_with("INSERT INTO conversations (user_id) VALUES(?);", (1,))
    mock_db.execute.assert_called_with('COMMIT')

def test_post_message(mock_db, mock_openai):
    mock_db.fetchall.return_value = [("user", "Hello"), ("assistant", "Hi there!")]
    response = client.post("/conversation/message", json={"prompt": "How are you?"})
    assert response.status_code == 200
    assert response.content == b"test response"
    mock_db.execute.assert_called_with("SELECT `role` , message FROM conversation_posts WHERE conversation_id = ? ORDER BY posted_at;", (1,))

def test_post_message_stream(mock_db, mock_openai):
    mock_db.fetchall.return_value = [("user", "Hello"), ("assistant", "Hi there!")]
    response = client.post("/conversation/messageStream", json={"prompt": "How are you?"})
    assert response.status_code == 200
    assert response.content == b"test response"
    mock_db.execute.assert_called_with("SELECT `role` , message FROM conversation_posts WHERE conversation_id = ? ORDER BY posted_at;", (1,))

def test_generate(mock_openai):
    messages = [{"role": "user", "content": "Hello"}]
    result = list(generate("gpt-4o-mini", 1, messages, "How are you?"))
    assert result == ["test response"]
    mock_openai.chat.completions.create.assert_called_with(model="gpt-4o-mini", messages=messages + [{"role": "user", "content": "How are you?"}], stream=True)

def test_get_conversation_id(mock_db):
    mock_db.fetchone.return_value = (1,)
    conversation_id = get_conversation_id(1, mock_db)
    assert conversation_id == 1
    mock_db.execute.assert_called_with("SELECT MAX(id) as id FROM conversations WHERE user_id = ?;", (1,))
"""
