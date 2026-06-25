from db.session import AsyncSession
from schemas.user import CreateUser, LoginUser
from models.users import User
from core.exceptions import AuthError
from core.security import hash_password, verify_password
from core.security import create_access_token
from sqlalchemy import select


async def auth_service_register_user(data:CreateUser, db:AsyncSession)->User:
    email = data.email
    result = await db.execute(
        select(User).filter_by(email = email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise AuthError("The user already exists, please login")
    
    password = data.password
    hashed_password = hash_password(password)

    new_user = User(
        email = email,
        password_hash = hashed_password
    )

    try:
        db.add(new_user)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise AuthError("Failed to register user") from e

    await db.refresh(new_user)    
    return new_user

    

async def auth_service_login_user(data:LoginUser, db:AsyncSession)->dict:
    email = data.email
    password=data.password

    # user = await db.query(User).filter_by(email = email).first()
    result = await db.execute(
        select(User).filter_by(email = email)
    )
    user = result.scalar_one_or_none()


    if not user:
        raise AuthError("Invalid credentials")
    if not verify_password(password, user.password_hash):
        raise AuthError("Invalid credentials")
    
    payload = {
        "sub":str(user.id)
    }

    access_token = create_access_token(data= payload)
    return {
        "access_token":access_token,
        "token_type":"bearer"
    }