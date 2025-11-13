from sqlalchemy import Column, Float, Integer, String, Text

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    jobTitle = Column(String(200), nullable=False)
    wage = Column(Float, nullable=False)
    city = Column(String(100), nullable=False)
    gender = Column(String(50), nullable=False)
    audioScript = Column(Text, nullable=False)  # base64 string or file path
    status = Column(String(20), default="open")  # open/closed

