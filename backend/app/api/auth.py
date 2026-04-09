from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from bson import ObjectId
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.database import get_database
from app.models.user import UserCreate, UserOut, Token, UserInDB
from app.core.config import settings
import secrets

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(user_in: UserCreate, db=Depends(get_database)):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    # Create new user
    user_data = user_in.model_dump()
    password = user_data.pop("password")
    user_data["hashed_password"] = get_password_hash(password)
    # We'll use datetime in UserInDB
    
    user_record = UserInDB(**user_data)
    result = await db.users.insert_one(user_record.model_dump())
    
    created_user = await db.users.find_one({"_id": result.inserted_id})
    # Convert ObjectId to string for the response model
    created_user["_id"] = str(created_user["_id"])
    return created_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_database)):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user["email"], expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(email: str, db=Depends(get_database)):
    user = await db.users.find_one({"email": email})
    if not user:
        # We don't want to leak if a user exists, but for this app we'll just return success
        return {"message": "If an account exists with this email, you will receive a reset link shortly."}
    
    # Generate mock token
    reset_token = secrets.token_urlsafe(32)
    # In a real app, save this token to DB with expiry and send email
    print(f"DEBUG: Reset token for {email}: {reset_token}")
    
    return {"message": "If an account exists with this email, you will receive a reset link shortly."}
