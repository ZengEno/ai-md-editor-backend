import os
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from fastapi import status
from motor.motor_asyncio import AsyncIOMotorDatabase

from database.db_classes import UserProfile
from database.db import db


SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="login")


class RegisterRequest(BaseModel):
    email: str
    user_nickname: str
    password: str


class JWTPayload(BaseModel):
    data: dict
    iat: datetime
    exp: datetime
    is_refresh: bool


async def fetch_user_profile(identifier: str):
    query = {"$or": [{"email": identifier}, {"user_id": identifier}]}
    document = await db.user_profiles.find_one(query)
    if document:
        return UserProfile(**document)
    else:
        return None

# Get the next registration counts


async def registration_counter(db: AsyncIOMotorDatabase):
    counter_doc = await db.app_statistics.find_one_and_update(
        {'name': 'registration_count'},
        {'$inc': {'value': 1}},
        return_document=True
    )
    
    if counter_doc is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get registration count")
    
    return counter_doc['value']


def create_jwt_token(data: dict, expire_delta: timedelta, is_refresh: bool = False):
    issued_at = datetime.now().timestamp()
    expiration_time = (datetime.now() + expire_delta).timestamp()
    payload = JWTPayload(
        data=data,
        iat=issued_at,
        exp=expiration_time,
        is_refresh=is_refresh
    )

    jwt_token = jwt.encode(payload.model_dump(),
                           key=SECRET_KEY, algorithm=ALGORITHM)
    return jwt_token, expiration_time


def validate_jwt_and_get_pyaload(jwt_token: str = Depends(oauth2_bearer)):
    try:
        # validate jwt_token
        payload = jwt.decode(jwt_token, key=SECRET_KEY, algorithms=[ALGORITHM])

        # check if the token has expired
        if datetime.now().timestamp() > payload['exp']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token has expired',
                headers={"WWW-Authenticate": "Bearer"})

        # make sure the payload data has user_id
        data = payload.get('data')
        if data['user_id'] is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='No user_id provided',
                headers={"WWW-Authenticate": "Bearer"})
        else:
            return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={"WWW-Authenticate": "Bearer"})


async def validate_jwt_and_fetch_user_profile(payload: dict = Depends(validate_jwt_and_get_pyaload),
                                              jwt_token: str = Depends(oauth2_bearer)):
    # fetch user profile
    user_profile = await fetch_user_profile(identifier=payload['data']['user_id'])

    # validate user profile
    if user_profile is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not find user')

    # validate refresh token if is_refresh is true
    if payload['is_refresh']:
        if user_profile.refresh_token != jwt_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token not match')

    return user_profile
