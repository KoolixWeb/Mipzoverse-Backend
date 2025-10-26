from fastapi import APIRouter, HTTPException, status, Depends
from database import users_collection
from schemas.user import UserCreate, UserLogin, Token, UserResponse
from utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from bson import ObjectId
from jose import jwt, JWTError
from config import settings
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    # Check if email already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = hash_password(user.password)
    user_dict = {
        "email": user.email,
        "mobile": user.mobile,
        "hashed_password": hashed_password,
        "role": "student",
        "created_at": datetime.utcnow()  # Add timestamp
    }
    
    result = await users_collection.insert_one(user_dict)
    user_id = str(result.inserted_id)

    # Generate tokens
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "role": "student"
    }

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    # Find user by email only
    db_user = await users_collection.find_one({"email": user.email})
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    user_id = str(db_user["_id"])
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "role": db_user["role"]
    }

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "mobile": current_user["mobile"],
        "role": current_user["role"],
        "created_at": current_user["created_at"]
    }