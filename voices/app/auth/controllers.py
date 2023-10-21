from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from voices.app.core.exceptions import (
    EmailTakenError,
    ObjectNotFoundError,
    PasswordMatchError,
    UserNotFoundError,
)
from voices.app.core.protocol import Response
from voices.app.friends.models import Friend, RelationshipType
from voices.auth.hash import get_password_hash, verify_password
from voices.auth.jwt_token import (
    JWTBearer,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from voices.chat import create_user, login_user
from voices.db.connection import Transaction
from voices.mail.confirm_email import async_confirm_email
from voices.redis import Redis

from .models import User
from .views import (
    CheckUserLogin,
    CityListView,
    OwnProfileView,
    ProfileUpdateView,
    ProfileView,
    Token,
    TokenData,
    TokenView,
    UserLogin,
    UserRegister,
)

router = APIRouter()


@router.post("/registration", response_model=Response[TokenView])
async def register_user(body: UserRegister):
    async with Transaction():
        user = await User.get_by_email(body.email)
        if user:
            raise EmailTakenError

        user = await User.insert_data(
            email=body.email,
            hashed_password=get_password_hash(body.password),
            first_name=body.first_name,
            last_name=body.last_name,
            city=body.city,
        )

        access_token, exp = create_access_token(TokenData(sub=user.id.hex, role=user.role))
        refresh_token = create_refresh_token(TokenData(sub=user.id.hex, role=user.role))

        try:
            await create_user(user_id=user.id, email=user.email)
            rocketchat_response = await login_user(user_id=user.id)
            json_response: dict = rocketchat_response.json()
        except Exception:
            json_response = {"data": {"authToken": "token"}}

        return Response(
            payload=TokenView(
                access_token=access_token,
                refresh_token=refresh_token,
                rocketchat_user_id=user.id.hex,
                rocketchat_auth_token=json_response["data"]["authToken"],
                exp=exp,
                user_id=str(user.id),
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

    if not user or user.deleted_at:
        raise UserNotFoundError
    if not verify_password(body.password, user.hashed_password):
        raise PasswordMatchError

    access_token, exp = create_access_token(TokenData(sub=user.id.hex, role=user.role))
    refresh_token = create_refresh_token(TokenData(sub=user.id.hex, role=user.role))

    try:
        rocketchat_response = await login_user(user_id=user.id)
        if rocketchat_response.status_code != 200:
            await create_user(user_id=user.id, email=user.email)
            rocketchat_response = await login_user(user_id=user.id)

        json_response = rocketchat_response.json()

    except Exception:
        json_response = {"data": {"authToken": "token"}}

    return Response(
        payload=TokenView(
            access_token=access_token,
            refresh_token=refresh_token,
            rocketchat_user_id=user.id.hex,
            rocketchat_auth_token=json_response.get("data", {}).get("authToken", ""),
            exp=exp,
            user_id=str(user.id),
        ),
    )


@router.post("/refresh-token", response_model=Response[TokenView])
async def post_refresh_token(body: Token):
    _token = decode_token(body.refresh_token)
    async with Transaction():
        user = await User.get_by_id(_token.sub)

    if not user:
        raise UserNotFoundError

    access_token, exp = create_access_token(TokenData(sub=user.id.hex, role=user.role))
    refresh_token = create_refresh_token(TokenData(sub=user.id.hex, role=user.role))

    return Response(
        payload=TokenView(
            access_token=access_token,
            refresh_token=refresh_token,
            rocketchat_user_id=user.id.hex,
            rocketchat_auth_token="",
            exp=exp,
            user_id=str(user.id),
        ),
    )


@router.patch("/profile", response_model=Response[ProfileView])  # TODO: to profile module
async def update_profile(body: ProfileUpdateView, token: TokenData = Depends(JWTBearer())):
    unset = body.dict(exclude_unset=True)

    async with Transaction():
        user = await User.update_profile(unset, user_id=token.sub)

    return Response(payload=ProfileView.from_orm(user))


@router.get("/profile", response_model=Response[OwnProfileView])
async def get_profile(token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        user = await User.get_by_id(id=token.sub)

    return Response(payload=OwnProfileView.from_orm(user))


@router.delete("/profile", response_model=Response[ProfileView])  # TODO: to profile module
async def delete_profile(token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await User.delete_profile(user_id=token.sub)

    return Response()


@router.get("/profile/{user_id}", response_model=Response[ProfileView])
async def get_user_profile(user_id: str, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        user = await User.get_profile(user_id=user_id)
        friend = await Friend.get_friend(user_id=token.sub, profile_id=user_id)

        if friend and friend.relationship_type == RelationshipType.NOT_APPROVED:
            if friend.user_id.hex == token.sub:
                friend.relationship_type = RelationshipType.FOLLOWER  # profile user is follower for this user

        if not user:
            raise ObjectNotFoundError

    return Response(
        payload=ProfileView(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            image_url=user.image_url,
            city=user.city,
            district=user.district,
            birthdate=user.birthdate,
            relationship_type=friend.relationship_type if friend else None,
            email=user.email,
        )
    )


@router.get("/cities", response_model=Response[CityListView])
def get_cites():
    return Response(
        payload=CityListView(cities=User.City.all()),
    )


@router.post("/confirm-email", response_model=Response)  # TODO: to mail module
async def send_confirm_email(token: TokenData = Depends(JWTBearer())):
    user_id = token.sub
    async with Transaction():  # TODO: auto transaction
        user_email = await User.get_email_by_id(id=user_id)

        email_token = await Redis.generate_confirm_email_token(user_id=user_id)
        await async_confirm_email(user_id=user_id, email_token=email_token, recipient_email=user_email)
    # signature("confirm_email").apply_async(
    #     kwargs=dict(user_id=user_id, email_token=email_token, recipient_email=user_email),
    # )
    return Response()


@router.get("/confirm-email/{user_id}/{email_token}")
async def get_confirm_email(user_id: str, email_token: str):
    async with Transaction():
        user_email = await User.get_email_by_id(id=user_id)

        cache_value = await Redis.get_confirm_email_token(user_id=user_id)

        if user_email and email_token and cache_value == email_token:
            await User.confirm_email(user_id=user_id)
            return HTMLResponse(f"<html><body>Адрес электронной почты <b>{user_email}</b> подтверждён</body></html>")
        # TODO: email already confirmed
        return HTMLResponse("<html><body>Ссылка недействительна или токен доступа истёк</body></html>")
