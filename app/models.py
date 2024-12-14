from sqlmodel import SQLModel, Field
from typing import Optional, Union
from pydantic import EmailStr, Field as PydanticField, field_validator, root_validator

class UserBase(SQLModel):
    first_name: str
    last_name: str
    username: str = PydanticField(..., min_length=3, max_length=50)
    email: EmailStr
    mobile: str = PydanticField(..., pattern=r'^\+?[1-9]\d{1,14}$')  # Updated from regex to pattern

class UserCreate(UserBase):
    password: str

class UserLogin(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    password: str

    @root_validator(pre=True)
    def check_one_field(cls, values):
        # Collect all identifiers into a list
        identifiers = [values.get('username'), values.get('email'), values.get('mobile')]
        
        # Check that at least one of username, email, or mobile is provided
        if not any(identifiers):
            raise ValueError("At least one of username, email, or mobile must be provided.")
        
        # Check that only one of the fields is filled
        if sum(bool(x) for x in identifiers) > 1:
            raise ValueError("Only one of username, email, or mobile must be provided.")
        
        return values
    
class UserRead(UserBase):
    id: int

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
