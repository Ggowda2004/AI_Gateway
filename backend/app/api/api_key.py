from fastapi import APIRouter, Depends, status, HTTPException
from schemas.api_key import APIKeyResponse, MakeAPIKey, APIKeyCreationResponse
from db.session import get_db, AsyncSession
from services.api_key_services import store_api_key, revoke_api_key
from models.users import User
from models.api_keys import APIKey
from dependencies.auth_dependency import get_current_user
from sqlalchemy import select
from typing import List


router2 = APIRouter(
    prefix="/key",
    tags=["Authentication"]
)

@router2.post("/",response_model=APIKeyCreationResponse, summary="Create a new API key", status_code=status.HTTP_201_CREATED
)
async def create_key(api_key_data:MakeAPIKey, current_user:User=Depends(get_current_user), db:AsyncSession = Depends(get_db)):
    user_id=current_user.id
    key_details=await store_api_key(api_key_data, db, user_id)
    return key_details



@router2.get("/",response_model=List[APIKeyResponse], summary="List all api keys", status_code=status.HTTP_200_OK)
async def list_keys(db:AsyncSession = Depends(get_db), current_user:User=Depends(get_current_user)):
    result = await db.execute(
        select(APIKey).filter_by(user_id=current_user.id)
    )
    return result.scalars().all()


@router2.delete("/{key_id}", summary="Revoke an API key", status_code=status.HTTP_200_OK)
async def revoke_key(key_id:str, db:AsyncSession = Depends(get_db), current_user:User=Depends(get_current_user)):
    try:
        user_id=current_user.id
        key = await db.get(APIKey, key_id)
        if not key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    message = await revoke_api_key(db, key_id, user_id)
    return {"message": message}