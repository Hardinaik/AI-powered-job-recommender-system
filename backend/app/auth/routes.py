from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import SignupRequest,LoginResponse,LoginRequest
from app.utils import hash_password,verify_password,create_access_token
#from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Auth"])

def authenticate_user(user: User):
    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "role": user.user_role
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.user_role
    }



@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # Check email
    existing_user = db.query(User).filter(User.email == data.email).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        fullname=data.fullname,
        email=data.email,
        password_hash=hash_password(data.password),
        user_role=data.user_role
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return authenticate_user(user)



@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    return authenticate_user(user)


