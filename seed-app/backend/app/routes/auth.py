from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_token
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.member_service import get_member_by_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    member = get_member_by_email(db, request.email)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No member found with this email",
        )
    token = create_token(member.id, member.full_name)
    return TokenResponse(
        access_token=token,
        member_id=member.id,
        member_name=member.full_name,
    )
