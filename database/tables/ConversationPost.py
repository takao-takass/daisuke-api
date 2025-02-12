from ..database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class ConversationPost(Base):
    __tablename__ = "conversation_posts"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String, index=False)
    message = Column(String, index=False)
    posted_at = Column(DateTime, index=False, server_default="now()")