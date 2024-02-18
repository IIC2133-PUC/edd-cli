from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .settings import settings

auth_scheme = HTTPBearer()

Credentials = Annotated[HTTPAuthorizationCredentials, Depends(auth_scheme)]


def verify_secret(credentials: Credentials):
    if credentials.credentials != settings.secret:
        raise HTTPException(status_code=403, detail="Invalid secret")
