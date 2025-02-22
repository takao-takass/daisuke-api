from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from auth import fake_hash_password, fake_users_db, UserInDB, User, get_current_active_user, get_current_user

router = APIRouter()

@router.post("/auth/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="ユーザー名またはパスワードが正しくありません。")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="ユーザー名またはパスワードが正しくありません。")

    return {"access_token": user.username, "token_type": "bearer"}

@router.get("/auth/username/")
async def read_items(current_user: User = Depends(get_current_user)):
    return {"User Name": current_user.username}

@router.get("/auth/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user