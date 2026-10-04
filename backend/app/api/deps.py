import uuid

from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import ALGORITHM
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def _decode_user_id(token: str, credentials_exception: HTTPException) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        return uuid.UUID(subject)
    except (JWTError, ValueError) as exc:
        raise credentials_exception from exc


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = _decode_user_id(token, credentials_exception)
    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_user_ws(websocket: WebSocket, db: Session = Depends(get_db)) -> User:
    """WebSocket equivalent of get_current_user. Browsers can't set custom
    headers on the WS upgrade request, so the token travels as a query param
    (?token=...) instead of an Authorization header."""
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    token = websocket.query_params.get("token")
    if not token:
        raise credentials_exception
    user_id = _decode_user_id(token, credentials_exception)
    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user
