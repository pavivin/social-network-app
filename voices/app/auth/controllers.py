from fastapi import APIRouter

from voices.auth.hash import get_password_hash, verify_password
from voices.auth.jwt_token import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from voices.db.connection import Transaction
from voices.exceptions import PasswordMatchError, UserNotFoundError
from voices.protocol import Response

from .models import User
from .views import Token, TokenData, UserLogin

router = APIRouter()


@router.post("/registration", response_model=Response[Token])
async def register_user(body: UserLogin):
    async with Transaction():
        user = await User.get_by_email(body.email)
        if user:
            return Response(code=400, message="Email already taken")

        await User.insert_data(email=body.email, hashed_password=get_password_hash(body.password))

    access_token = create_access_token(TokenData(email=body.email, role="USER"))
    refresh_token = create_refresh_token(TokenData(email=body.email, role="USER"))

    return Response(
        payload=Token(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/login", response_model=Response[Token])
async def authenticate_user(body: UserLogin):
    async with Transaction():
        user = await User.get_by_email(body.email)

    if not user:
        raise UserNotFoundError
    if not verify_password(body.password, user.hashed_password):
        raise PasswordMatchError

    access_token = create_access_token(TokenData(email=user.email, role=user.role))
    refresh_token = create_refresh_token(TokenData(email=user.email, role=user.role))

    return Response(
        payload=Token(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/refresh-token", response_model=Response[Token])
async def post_refresh_token(body: Token):
    _token = decode_token(body.refresh_token)
    user = await User.get_by_email(_token.email)
    if not user:
        raise UserNotFoundError

    access_token = create_access_token(TokenData(fullname=user.fullname, email=user.email, role=user.role))
    refresh_token = create_refresh_token(TokenData(fullname=user.fullname, email=user.email, role=user.role))

    return Response(
        payload=Token(access_token=access_token, refresh_token=refresh_token),
    )
