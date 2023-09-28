from datetime import datetime, timedelta

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from pydantic import ValidationError

from voices.app.auth.views import TokenData
from voices.app.core.exceptions import (
    JWTDecodeError,
    JWTExpiredSignatureError,
    UnauthorizedError,
)
from voices.config import settings


def create_access_token(data: TokenData) -> tuple[str, datetime]:
    expire = datetime.utcnow() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRES)
    data.exp = expire
    encoded_jwt = jwt.encode(dict(data), settings.AUTH_PRIVATE_KEY_DATA, algorithm=settings.AUTH_ALGORITHM)
    return encoded_jwt, expire


def create_refresh_token(data: TokenData) -> str:
    expire = datetime.utcnow() + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRES)
    data.exp = expire
    encoded_jwt = jwt.encode(dict(data), settings.AUTH_PRIVATE_KEY_DATA, algorithm=settings.AUTH_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.AUTH_PUBLIC_KEY_DATA, algorithms=[settings.AUTH_ALGORITHM])
        if not payload:
            raise UnauthorizedError
        token_data = TokenData(**payload)
        if datetime.utcnow() > token_data.exp.replace(tzinfo=None):
            raise UnauthorizedError
    except ExpiredSignatureError as e:
        raise JWTExpiredSignatureError from e
    except (JWTError, ValidationError) as e:
        raise JWTDecodeError from e
    return token_data


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True, required: bool = True):
        self.required = required
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        if not request.headers.get("Authorization") and not self.required:
            return None
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            return decode_token(credentials.credentials)
        raise HTTPException(status_code=403, detail="Invalid authorization code.")
