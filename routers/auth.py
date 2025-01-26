from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from database.db import db
from database.db_classes import UserInfo
from .id_utils import generate_user_id
from .auth_utils import (
    RegisterRequest, fetch_user_profile, UserProfile, registration_counter,
    create_jwt_token, validate_jwt_and_fetch_user_profile)


auth_router = APIRouter(tags=["User Authentication"])

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 1

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 注册用户
@auth_router.post("/register",
                  status_code=status.HTTP_201_CREATED,
                  summary="Register a new user",
                  description="Register a new user with an email and a password")
async def register_user(register_request: RegisterRequest):
    # 1. 检查邮箱是否已经注册
    existing_user = await fetch_user_profile(identifier=register_request.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already registered")

    # 2. 创建用户
    user_profile = UserProfile(
        user_id=generate_user_id(await registration_counter(db)),
        user_nickname=register_request.user_nickname,
        email=register_request.email,
        hashed_password=pwd_context.hash(register_request.password),
        created_at=datetime.now(),
        last_login=datetime.now()
    )

    result = await db.user_profiles.insert_one(user_profile.model_dump())

    # 3. 返回用户信息
    if result.inserted_id:
        return UserInfo(**user_profile.model_dump())
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to register user")


# 登录
@auth_router.post("/login",
                  status_code=status.HTTP_200_OK,
                  summary="Login with email and password",
                  description=f'Access token expires in {ACCESS_TOKEN_EXPIRE_MINUTES} minutes, and refresh token expires in {REFRESH_TOKEN_EXPIRE_DAYS} days')
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. 检查邮箱是否注册, 并检查密码是否正确, 并检查用户是否被锁定
    email = form_data.username  # 在这个OAuth2PasswordRequestForm中，username就是邮箱
    password = form_data.password
    user_profile = await fetch_user_profile(identifier=email)

    if not user_profile or not pwd_context.verify(password, user_profile.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    elif user_profile.inactive:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User is inactive",
                            headers={"WWW-Authenticate": "Bearer"})

    # 2. 生成token
    access_token, access_expiration_time = create_jwt_token(data={"user_id": user_profile.user_id,
                                                                  "user_nickname": user_profile.user_nickname},
                                                            expire_delta=timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        is_refresh=False)
    refresh_token, refresh_expiration_time = create_jwt_token(data={"user_id": user_profile.user_id,
                                                                    "user_nickname": user_profile.user_nickname},
                                                              expire_delta=timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS),
        is_refresh=True)

    # 3. 保存token到数据库
    await db.user_profiles.update_one(
        {"user_id": user_profile.user_id},
        {"$set": {"refresh_token": refresh_token, "last_login": datetime.now()}}
    )

    # 4. 返回token
    return JSONResponse(content={"messages": "Login successful",
                                 "access_token": access_token,
                                 "access_expiration_time": access_expiration_time,
                                 "refresh_token": refresh_token,
                                 "refresh_expiration_time": refresh_expiration_time,
                                 "token_type": "bearer",
                                 "user": {
                                     "user_id": user_profile.user_id,
                                     "user_nickname": user_profile.user_nickname
                                 }})


# 刷新token
@auth_router.get("/refresh",
                 status_code=status.HTTP_200_OK,
                 summary="Refresh access token",
                 description="Refresh access token with refresh token")
async def refresh_token(user_profile: UserProfile = Depends(validate_jwt_and_fetch_user_profile)):
    new_access_token, access_expiration_time = create_jwt_token(data={"user_id": user_profile.user_id,
                                                                      "user_nickname": user_profile.user_nickname},
                                                                expire_delta=timedelta(
                                                                    minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                                                                is_refresh=False)
    return JSONResponse(content={"message": "Refresh successful",
                                 "access_token": new_access_token,
                                 "access_expiration_time": access_expiration_time,
                                 "token_type": "bearer"})


# 登出
@auth_router.post("/logout",
                  status_code=status.HTTP_200_OK,
                  summary="Logout",
                  description="Logout a user. Remember to remove tokens from client side")
async def logout_user(user_profile: UserProfile = Depends(validate_jwt_and_fetch_user_profile)):
    await db.user_profiles.update_one(
        {"user_id": user_profile.user_id},
        {"$set": {"refresh_token": None}}
    )
    return JSONResponse(content={"message": "Logout successful"})


# 获取用户信息
@auth_router.get("/user/my_info",
                 status_code=status.HTTP_200_OK,
                 summary="Get user information",
                 description="Get user information")
async def get_user_info(user_profile: UserProfile = Depends(validate_jwt_and_fetch_user_profile)):
    return JSONResponse(content={"user_id": user_profile.user_id,
                                 "user_nickname": user_profile.user_nickname,
                                 "email": user_profile.email,
                                 "created_at": str(user_profile.created_at),
                                 "last_login": str(user_profile.last_login)})
