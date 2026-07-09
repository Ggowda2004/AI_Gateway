from pwdlib import PasswordHash
import jwt
from core.config import settings
from datetime import datetime, timezone, timedelta
from core.exceptions import AuthError

#Initialize the global hashing engine
password_hash = PasswordHash.recommended()

def hash_password(password:str)->str:
    return password_hash.hash(password)

def verify_password(plain_password:str, hashed_password:str)->bool:
    return password_hash.verify(plain_password,hashed_password)



def create_access_token(data:dict)->str:
    to_encode = data
    expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY_MINUTES)
    to_encode.update({'exp':expiry})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        settings.ALGORITHM
    )

    return encoded_jwt

def verify_access_token(token:str)->dict|None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except(jwt.ExpiredSignatureError):
        raise AuthError("The token is expired")
    except(jwt.InvalidKeyError):
        raise AuthError("Invalid key error")
    

def hash_api_key(api_key:str)->str:
    """Hashes a plain-text API key using Argon2id."""
    return password_hash.hash(api_key)