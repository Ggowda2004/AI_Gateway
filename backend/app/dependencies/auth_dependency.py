from db.session import AsyncSession, get_db
from core.security import verify_access_token
from core.exceptions import AuthError
import uuid
from models.users import User
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

async def validate_token(token:str, db:AsyncSession):    
    payload = verify_access_token(token)
    if not payload:
        raise AuthError("Invalid token payload")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Invalid token: missing user ID")
        
    try:
        user_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid user ID format in token"
    )
    user = await db.get(User, user_id)
        #db.get() is the superior choice over db.execute(select(...)) when fetching a record by its primary key:
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
    



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token:str = Depends(oauth2_scheme), db:AsyncSession = Depends(get_db)) -> User:
    try:
        return await validate_token(token, db)
    except AuthError as e:
        # Securely translate internal service errors into proper 401 HTTP codes
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )