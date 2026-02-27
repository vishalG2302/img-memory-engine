from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class ImageEpisode(Base):
    __tablename__ = "image_episode"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, ForeignKey("image_raw.id"), nullable=False)
    user_id = Column(String, nullable=False)
    source = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)