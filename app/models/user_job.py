from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserJob(Base):
    __tablename__ = "user_jobs"

    userId = Column(Integer, ForeignKey("users.id"), primary_key=True)
    jobId = Column(Integer, ForeignKey("jobs.id"), primary_key=True)
    status = Column(String(20), nullable=False)  # applied, rejected, etc.

    # Relationships
    user = relationship("User", backref="user_jobs")
    job = relationship("Job", backref="user_jobs")

