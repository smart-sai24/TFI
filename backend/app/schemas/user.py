from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    name: str | None = None
    role: str

class UserCreate(UserBase):
    uid: str

class UserResponse(UserBase):
    uid: str
    is_active: bool

    model_config = {'from_attributes': True}
