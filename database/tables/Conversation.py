from ..database import Base
from sqlalchemy import Column, Integer, String

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    model_name = Column(String(length=50), index=False)