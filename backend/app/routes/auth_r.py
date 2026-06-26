from fastapi import APIRouter, Depends, status, HTTPException
from schemas.user import CreateUser, LoginUser
from db.session import AsyncSession, get_db
from services.auth_services import auth_service_register_user, auth_service_login_user
from core.exceptions import AuthError
from fastapi.security import OAuth2PasswordRequestForm
from models.users import User
from dependencies.auth_dependency import get_current_user


router1 = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router1.post("/register",summary="Register the user", status_code=status.HTTP_200_OK)
async def register_user(user_date:CreateUser,db:AsyncSession = Depends(get_db))->dict:
    try:
        new_user = await auth_service_register_user(user_date, db)
        return{
            "message":"User registered successfully",
            "user_id":new_user.id,
            "email": new_user.email
        }
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    
@router1.post("/login",summary="Login endpoint", status_code=status.HTTP_200_OK)
async def login_user(form_data:OAuth2PasswordRequestForm = Depends(), db:AsyncSession = Depends(get_db))->dict:
    try:
        user_data = LoginUser(email=form_data.username, password=form_data.password)
        token_data = await auth_service_login_user(user_data,db)
        return token_data
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="bro you are not registered")

@router1.get("/me",summary="Get current user details", status_code=status.HTTP_200_OK)
async def verify_me(current_user: User = Depends(get_current_user))->dict:
    return {
        "user_id": current_user.id,
        "email": current_user.email,
    }
    