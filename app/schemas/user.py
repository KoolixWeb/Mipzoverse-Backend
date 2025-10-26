from pydantic import BaseModel, EmailStr, field_validator
import re

class UserBase(BaseModel):
    email: EmailStr
    mobile: str
    
    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, v):
        if v:
            # Remove spaces and dashes
            v = re.sub(r'[\s\-]', '', v)
            # Basic validation for international format
            if not re.match(r'^\+?[1-9]\d{1,14}$', v):
                raise ValueError('Invalid mobile number format. Use international format (e.g., +911234567890)')
        return v

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None

class UserResponse(BaseModel):
    email: str
    mobile: str
    role: str