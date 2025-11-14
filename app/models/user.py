from sqlalchemy import Column, Integer, String

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=True)

