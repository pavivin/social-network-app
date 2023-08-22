from fastapi import APIRouter, Depends

from voices.app.core.exceptions import (
    EmailTakenError,
    PasswordMatchError,
    UserNotFoundError,
)
from voices.app.core.protocol import Response
from voices.auth.hash import get_password_hash, verify_password
from voices.auth.jwt_token import (
    JWTBearer,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from voices.chat import create_user, login_user
from voices.db.connection import Transaction

from .models import User
from .views import CheckUserLogin, ProfileView, Token, TokenData, TokenView, UserLogin

router = APIRouter()


@router.post("/registration", response_model=Response[TokenView])
async def register_user(body: UserLogin):
    async with Transaction():
        user = await User.get_by_email(body.email)
        if user:
            raise EmailTakenError

        user = await User.insert_data(email=body.email, hashed_password=get_password_hash(body.password))

        access_token, exp = create_access_token(TokenData(sub=user.id.hex, email=body.email, role=user.role))
        refresh_token = create_refresh_token(TokenData(sub=user.id.hex, email=body.email, role=user.role))

        await create_user(user_id=user.id, email=user.email)
        rocketchat_response = await login_user(user_id=user.id)
        json_response = rocketchat_response.json()

        return Response(
            payload=TokenView(
                access_token=access_token,
                refresh_token=refresh_token,
                rocketchat_user_id=user.id.hex,
                rocketchat_auth_token=json_response["data"]["authToken"],
                exp=exp,
            ),
        )


@router.post("/check-email", response_model=Response)
async def check_mail(body: CheckUserLogin):
    async with Transaction():
        user = await User.get_by_email(body.email)
        if user:
            raise EmailTakenError

    return Response()


@router.post("/login", response_model=Response[TokenView])
async def authenticate_user(body: UserLogin):
    async with Transaction():
        user = await User.get_by_email(body.email)

    if not user:
        raise UserNotFoundError
    if not verify_password(body.password, user.hashed_password):
        raise PasswordMatchError

    access_token, exp = create_access_token(TokenData(sub=user.id.hex, email=user.email, role=user.role))
    refresh_token = create_refresh_token(TokenData(sub=user.id.hex, email=user.email, role=user.role))

    rocketchat_response = await login_user(user_id=user.id)
    if rocketchat_response.status_code != 200:
        await create_user(user_id=user.id, email=user.email)
        rocketchat_response = await login_user(user_id=user.id)

    json_response = rocketchat_response.json()

    return Response(
        payload=TokenView(
            access_token=access_token,
            refresh_token=refresh_token,
            rocketchat_user_id=user.id.hex,
            rocketchat_auth_token=json_response["data"]["authToken"],
            exp=exp,
        ),
    )


@router.post("/refresh-token", response_model=Response[TokenView])
async def post_refresh_token(body: Token):
    _token = decode_token(body.refresh_token)
    async with Transaction():
        user = await User.get_by_id(_token.sub)

    if not user:
        raise UserNotFoundError

    access_token, exp = create_access_token(TokenData(sub=user.id.hex, email=user.email, role=user.role))
    refresh_token = create_refresh_token(TokenData(sub=user.id.hex, email=user.email, role=user.role))

    rocketchat_response = await login_user(user_id=user.id)

    if rocketchat_response.status_code != 200:
        await create_user(user_id=user.id, email=user.email)
        rocketchat_response = await login_user(user_id=user.id)

    json_response = rocketchat_response.json()

    return Response(
        payload=TokenView(
            access_token=access_token,
            refresh_token=refresh_token,
            rocketchat_user_id=user.id.hex,
            rocketchat_auth_token=json_response["data"]["authToken"],
            exp=exp,
        ),
    )


@router.patch("/profile", response_model=Response[ProfileView])
async def update_profile(body: ProfileView, token: TokenData = Depends(JWTBearer())):
    unset = body.dict(exclude_unset=True)

    async with Transaction():
        user = await User.update_profile(unset, user_id=token.sub)

    return Response(payload=ProfileView.from_orm(user))


@router.get("/profile", response_model=Response[ProfileView])
async def get_profile(token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        user = await User.get_by_id(id=token.sub)

    return Response(payload=ProfileView.from_orm(user))


@router.get("/profile/{user_id}", response_model=Response[ProfileView])
async def get_user_profile(user_id: str):
    async with Transaction():
        user = await User.get_by_id(id=user_id)

    return Response(payload=ProfileView.from_orm(user))
