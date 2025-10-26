from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import users_collection
from schemas.user import UserCreate, UserLogin, Token, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from utils.email import send_reset_code_email
from bson import ObjectId
from jose import jwt, JWTError
from config import settings
from datetime import datetime, timedelta
import random
import string

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def generate_reset_code():
    """Generate a 6-digit reset code"""
    return ''.join(random.choices(string.digits, k=6))

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
        "created_at": datetime.utcnow()
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

@router.post("/token", response_model=Token)
async def login_for_swagger(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2 uses 'username' field, but we treat it as email
    db_user = await users_collection.find_one({"email": form_data.username})
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, db_user["hashed_password"]):
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

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset code to user's email"""
    # Check if user exists
    user = await users_collection.find_one({"email": request.email})
    
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a reset code has been sent"}
    
    # Generate reset code
    reset_code = generate_reset_code()
    reset_code_expiry = datetime.utcnow() + timedelta(minutes=15)
    
    # Store reset code in database
    await users_collection.update_one(
        {"email": request.email},
        {
            "$set": {
                "reset_code": reset_code,
                "reset_code_expiry": reset_code_expiry
            }
        }
    )
    
    # Send email
    email_sent = send_reset_code_email(request.email, reset_code)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email. Please try again later."
        )
    
    return {"message": "If the email exists, a reset code has been sent"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using the code sent to email"""
    # Find user with matching email and reset code
    user = await users_collection.find_one({
        "email": request.email,
        "reset_code": request.code
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or reset code"
        )
    
    # Check if code has expired
    if user.get("reset_code_expiry") and user["reset_code_expiry"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired. Please request a new one."
        )
    
    # Hash new password
    hashed_password = hash_password(request.new_password)
    
    # Update password and remove reset code
    await users_collection.update_one(
        {"email": request.email},
        {
            "$set": {"hashed_password": hashed_password},
            "$unset": {"reset_code": "", "reset_code_expiry": ""}
        }
    )
    
    return {"message": "Password reset successful"}

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