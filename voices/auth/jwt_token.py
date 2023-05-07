from datetime import datetime, timedelta

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from pydantic import ValidationError

from voices.app.auth.views import TokenData
from voices.config import settings
from voices.exceptions import UnauthorizedError


def create_access_token(data: TokenData) -> str:
    expire = datetime.now() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRES)
    data.exp = expire
    encoded_jwt = jwt.encode(dict(data), settings.AUTH_PRIVATE_KEY_DATA, algorithm=settings.AUTH_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: TokenData) -> str:
    expire = datetime.now() + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRES)
    data.exp = expire
    encoded_jwt = jwt.encode(dict(data), settings.AUTH_PRIVATE_KEY_DATA, algorithm=settings.AUTH_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.AUTH_PUBLIC_KEY_DATA, algorithms=[settings.AUTH_ALGORITHM])
        if not payload:
            raise UnauthorizedError
        token_data = TokenData(**payload)
        if datetime.now() > token_data.exp.replace(tzinfo=None):
            raise UnauthorizedError
    except (JWTError, ExpiredSignatureError, ValidationError) as e:
        raise UnauthorizedError from e
    return token_data
