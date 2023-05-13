from fastapi import APIRouter, Depends, Query

from voices.auth.hash import get_password_hash, verify_password
from voices.auth.jwt_token import (
    JWTBearer,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from voices.db.connection import Transaction
from voices.exceptions import BadRequestError, PasswordMatchError, UserNotFoundError
from voices.protocol import Response

from .models import User
from .views import (
    ProfileUpdateView,
    ProfileView,
    SearchListView,
    Token,
    TokenData,
    UserLogin,
)

router = APIRouter()


@router.post("/registration", response_model=Response[Token])
async def register_user(body: UserLogin):
    async with Transaction():
        user = await User.get_by_email(body.email)
        if user:
            raise BadRequestError("Email already taken")

        user_id = await User.insert_data(email=body.email, hashed_password=get_password_hash(body.password))

    access_token = create_access_token(TokenData(sub=user_id.hex, email=body.email, role="USER"))
    refresh_token = create_refresh_token(TokenData(sub=user_id.hex, email=body.email, role="USER"))

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

    access_token = create_access_token(TokenData(sub=user.id.hex, email=user.email, role=user.role))
    refresh_token = create_refresh_token(TokenData(sub=user.id.hex, email=user.email, role=user.role))

    return Response(
        payload=Token(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/refresh-token", response_model=Response[Token])
async def post_refresh_token(body: Token):
    _token = decode_token(body.refresh_token)
    async with Transaction():
        user = await User.get_by_id(_token.sub)
    if not user:
        raise UserNotFoundError

    access_token = create_access_token(TokenData(sub=user.id, email=user.email, role=user.role))
    refresh_token = create_refresh_token(TokenData(sub=user.id, email=user.email, role=user.role))

    return Response(
        payload=Token(access_token=access_token, refresh_token=refresh_token),
    )


@router.patch("/profile", response_model=Response[ProfileView])
async def update_profile(body: ProfileUpdateView):
    unset = body.dict(exclude_unset=True)

    async with Transaction():
        user = await User.update_profile(unset)

    return Response(payload=ProfileView(email=user.email, role=user.role))


@router.get("/profile", response_model=Response[ProfileView])
async def get_profile(token: TokenData = Depends(JWTBearer())):
    return Response(payload=ProfileView(email=token.email, role=token.role))


@router.get("/search", response_model=Response[SearchListView])
async def search_by_pattern(pattern: str = Query(min_length=3)):
    async with Transaction():
        users = await User.search_by_pattern(pattern=pattern)
    return Response(payload=SearchListView(users=users))
