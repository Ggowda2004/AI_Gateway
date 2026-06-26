import secrets
from db.session import AsyncSession
from schemas.api_key import MakeAPIKey
from core.security import hash_api_key
from models.api_keys import APIKey
from core.security import AuthError
from sqlalchemy import select
from models.users import User
from core.security import verify_password

def generate_api_key()->str:
    raw_key = secrets.token_hex(32)
    key = f"kmgg_live_{raw_key}"

    return key

async def store_api_key(api_key_data:MakeAPIKey, db:AsyncSession, user_id:str)->dict:
    name = api_key_data.name
    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)

    new_key = APIKey(
        user_id=user_id,
        name=name,
        key_hash = hashed_key
    )

    try:
        db.add(new_key)#this is sync
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise AuthError("unable to store api key") from e
    await db.refresh(new_key)
    
    return {
        "key_id":new_key.id,
        "key_name":new_key.name,
        "raw_key":raw_key,
    }

async def revoke_api_key(db:AsyncSession, key_id:str, user_id:str)->str:
    # key_record = await db.query(APIKey).filter_by(id=key_id,user_id=user_id).first() -> wrong
    result = await db.execute(
        select(APIKey).filter_by(id=key_id, user_id=user_id)
    )
    key_record = result.scalar_one_or_none()


    if not key_record:
        raise AuthError("no key found")
    if not key_record.is_active:
        return f"user_id{user_id} key already revoked"
    key_record.is_active = False
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise AuthError("unable to revoke api key") from e
    await db.refresh(key_record)
    return f"user_id{user_id} key revoked successfully"

async def validate_api_key(db:AsyncSession, key:str) -> User:
    """
    Validates an API key by verifying it against stored hashes in the database.
    Returns the User associated with the valid key.
    """
    if not key.startswith("kmgg_live_"):
        raise AuthError("Invalid Key or No key match found")
    
    try:
        # Query all active keys with user relationship eagerly loaded
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(APIKey)
            .where(APIKey.is_active == True)
            .options(selectinload(APIKey.user))
        )
        active_keys = result.scalars().unique().all()
        
        # Verify the incoming key against each stored hash
        for key_record in active_keys:
            try:
                if verify_password(key, key_record.key_hash):
                    # Ensure user is loaded
                    user = key_record.user
                    if not user:
                        continue
                    return user
            except Exception:
                # Skip if verification fails for this key
                continue
        
        raise AuthError("Invalid Key or No key match found")
        
    except AuthError:
        raise
    except Exception as e:
        raise AuthError(f"Error validating API key: {str(e)}")