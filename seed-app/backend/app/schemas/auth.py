from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    member_id: int
    member_name: str
