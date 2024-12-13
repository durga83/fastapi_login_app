from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import EmailStr, Field as PydanticField

class UserBase(SQLModel):
    first_name: str
    last_name: str
    username: str = PydanticField(..., min_length=3, max_length=50)
    email: EmailStr
    mobile: str = PydanticField(..., pattern=r'^\+?[1-9]\d{1,14}$')  # Updated from regex to pattern

class UserCreate(UserBase):
    password: str

class UserLogin(SQLModel):
    username: str
    password: str

class UserRead(UserBase):
    id: int

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
