from datetime import datetime, timedelta

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from pydantic import ValidationError

from voices.app.auth.views import TokenData
from voices.app.core.exceptions import UnauthorizedError
from voices.config import settings


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


def decode_token(token: str, required: bool = True) -> TokenData:
    try:
        payload = jwt.decode(token, settings.AUTH_PUBLIC_KEY_DATA, algorithms=[settings.AUTH_ALGORITHM])
        if not payload and required:
            raise UnauthorizedError
        token_data = TokenData(**payload)
        if datetime.now() > token_data.exp.replace(tzinfo=None):
            raise UnauthorizedError
    except (JWTError, ExpiredSignatureError, ValidationError) as e:
        raise UnauthorizedError from e
    return token_data


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True, required: bool = True):
        self.required = required
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            return decode_token(credentials.credentials, required=self.required)
        raise HTTPException(status_code=403, detail="Invalid authorization code.")
