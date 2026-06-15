import os
import re

from fastmcp.exceptions import AuthorizationError
from fastmcp.server.dependencies import get_http_headers
from sqlalchemy.orm import Session

from app.core.security import TOKEN_TYPE_ACCESS, verify_token
from app.models.user import User

_BEARER_RE = re.compile(r"^Bearer\s+(.+)$", re.IGNORECASE)


def resolve_access_token() -> str | None:
    token = os.environ.get("BANVIRO_ACCESS_TOKEN", "").strip()
    if token:
        return token

    try:
        headers = get_http_headers()
    except RuntimeError:
        return None

    authorization = headers.get("authorization")
    if not authorization:
        return None

    match = _BEARER_RE.match(authorization)
    return match.group(1).strip() if match else None


def resolve_mcp_user(db: Session) -> User:
    token = resolve_access_token()
    if not token:
        raise AuthorizationError(
            "Authentication required. Set BANVIRO_ACCESS_TOKEN or send "
            "Authorization: Bearer <access_token>."
        )

    email = verify_token(token, TOKEN_TYPE_ACCESS)
    if email is None:
        raise AuthorizationError("Invalid or expired access token.")

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise AuthorizationError("User not found or inactive.")

    return user
