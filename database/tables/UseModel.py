from ..database import Base
from sqlalchemy import Column, Integer, String

class UseModel(Base):
    __tablename__ = "use_models"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    model_for_text_generation = Column(String, index=False)