from fastapi import Depends, HTTPException, status
from db.session import AsyncSession, get_db
from models.api_keys import APIKey
from fastapi.security import APIKeyHeader
from models.users import User
from services.api_key_services import validate_api_key
from core.exceptions import AuthError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_user_from_api_key(api_key: str = Depends(api_key_header_scheme), db: AsyncSession = Depends(get_db))->User:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key missing. Pass your key via 'X-API-Key' header"
        )
    try:
        user = await validate_api_key(db, api_key)
        return user
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid API Key: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to validate API Key"
        )


# bearer_scheme = HTTPBearer(auto_error=False)
# async def get_current_api_key_context(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),db: AsyncSession = Depends(get_db))->APIKey:
#     '''this dependency validates bearer token API Key against the DB.
#     Attaches the verified key object (and its related user) to the request context.'''
#     if not credentials or credentials.schema.lower() != "bearer":
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Missing or invalid Authorization header scheme. Use 'Bearer <api_key>'",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
        
#     try:
#         raw_api_key = credentials.credentials
#         key_record = await validate_api_key(db=db, key=raw_api_key)
#         return key_record
#     except AuthError as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=str(e),
#             headers={"WWW-Authenticate": "Bearer"},
#         )