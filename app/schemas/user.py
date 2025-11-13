from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    name: str
    city: str

    class Config:
        from_attributes = True

