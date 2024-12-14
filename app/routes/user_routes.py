from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_db
from app.models import User, UserCreate, UserLogin, UserRead
from app.utils.hashing import hash_password, verify_password
from app.utils.auth import create_access_token, create_refresh_token, verify_token
from datetime import timedelta

router = APIRouter(prefix="/user", tags=["User"])

# In-memory set to simulate storing used refresh tokens (Replace with DB or Cache in production)
used_refresh_tokens = set()


@router.post("/registration", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the user already exists
    existing_user = db.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    
    # Create a new user
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        mobile=user.mobile,
        password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    # Check if the user exists by username, email, or mobile
    db_user = (
        db.exec(
            select(User).where(
                (User.username == user.username) |  # Check for username
                (User.email == user.email) |        # Check for email
                (User.mobile == user.mobile)         # Check for mobile
            )
        )
    ).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    
    # Generate tokens
    access_token = create_access_token({"sub": db_user.username}, timedelta(hours=1))
    refresh_token = create_refresh_token({"sub": db_user.username})
    
    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
    }


@router.post("/renew_tokens")
def refresh_access_and_refresh_tokens(refresh_token: str, db: Session = Depends(get_db)):
    # Verify the refresh token
    payload = verify_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    
    user_id = payload["sub"]
    
    # Check if the refresh token has already been used
    if refresh_token in used_refresh_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has already been used")
    
    # Mark this refresh token as used
    used_refresh_tokens.add(refresh_token)
    
    # Generate new tokens
    new_access_token = create_access_token({"sub": user_id}, timedelta(hours=1))
    new_refresh_token = create_refresh_token({"sub": user_id})
    
    return {
        "accessToken": new_access_token,
        "refreshToken": new_refresh_token,
    }
