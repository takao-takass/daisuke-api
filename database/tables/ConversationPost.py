from ..database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text

class ConversationPost(Base):
    __tablename__ = "conversation_posts"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String(length=50), index=False)
    message = Column(String(length=5000), index=False)
    posted_at = Column(DateTime, index=False, server_default=text("CURRENT_TIMESTAMP"))