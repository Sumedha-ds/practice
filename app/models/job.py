from sqlalchemy import Column, Float, Integer, String, Text

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    jobUuid = Column(String(36), unique=True, index=True, nullable=True)
    jobTitle = Column(String(200), nullable=False)
    wage = Column(Float, nullable=False)
    city = Column(String(100), nullable=False)
    gender = Column(String(50), nullable=False)
    audioScript = Column(Text, nullable=False, default="")  # base64 string or file path
    audioFilePath = Column(String(255), nullable=True)
    status = Column(String(20), default="open")  # open/closed

