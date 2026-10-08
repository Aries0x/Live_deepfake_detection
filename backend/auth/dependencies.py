"""
Authentication & Authorization FastAPI Dependencies.
Implements JWT session validation from httpOnly cookies, permission verification,
contextual scope checks, and WebSocket handshake authentication.
"""
import time
import jwt
from typing import Dict, Any, Optional, Callable
from fastapi import Request, WebSocket, HTTPException, status, Depends
from backend.app.config import settings
from backend.auth.permissions import Permission, Role, can_perform
from backend.auth.models import UserStore, User
from backend.auth.security_audit import SecurityAuditLogger
from backend.app.logging_config import get_logger

logger = get_logger("auth_dependencies")

COOKIE_NAME = "securecall_session"


def create_session_jwt(user: User) -> str:
    """
    Creates a signed session JWT with role-specific expiration:
      - citizen: 8 hours (28,800s)
      - forensic_officer & judge: 30 minutes (1,800s, sliding)
      - admin: 30 minutes (1,800s)
    """
    now = int(time.time())
    if user.role == Role.CITIZEN:
        exp = now + (8 * 3600)
    elif user.role in (Role.FORENSIC_OFFICER, Role.JUDGE):
        exp = now + (30 * 60)
    elif user.role == Role.ADMIN:
        exp = now + (30 * 60)
    else:
        exp = now + 3600

    payload: Dict[str, Any] = {
        "user_id": user.id,
        "name": user.name,
        "role": user.role.value,
        "court_id": user.court_id,
        "assigned_cases": user.assigned_cases,
        "consent_given": user.consent_given,
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_session_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a session JWT.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as e:
        logger.debug("Session token decode failed", error=str(e))
        return None


def get_token_from_request(request: Request) -> Optional[str]:
    """Extracts session token from Bearer header, httpOnly cookie, or query param."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer = auth_header.split(" ", 1)[1].strip()
        if bearer:
            return bearer
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    return request.query_params.get("token")


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Retrieves authenticated user payload if session exists, else None."""
    # 1. Try Bearer header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer = auth_header.split(" ", 1)[1].strip()
        if bearer:
            payload = decode_session_jwt(bearer)
            if payload:
                return payload

    # 2. Try session cookie
    token = request.cookies.get(COOKIE_NAME)
    if token:
        payload = decode_session_jwt(token)
        if payload:
            return payload

    # 3. Try query param
    query_tok = request.query_params.get("token")
    if query_tok:
        payload = decode_session_jwt(query_tok)
        if payload:
            return payload

    return None


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Mandatory authentication dependency.
    Raises 401 Unauthorized if session is missing or expired.
    """
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to access this resource.",
        )
    return user


def require_permission(
    permission: Permission | str,
    scope_getter: Optional[Callable[[Request], Dict[str, Any]]] = None,
):
    """
    FastAPI dependency factory enforcing the RBAC permission matrix.
    Verifies user authentication, permission rules, and contextual scope.
    """
    async def dependency(request: Request, user: Dict[str, Any] = Depends(get_current_user)):
        context: Dict[str, Any] = {}
        if scope_getter:
            try:
                context = scope_getter(request)
            except Exception as e:
                logger.warning("Scope getter failed", error=str(e))

        allowed = can_perform(user=user, permission=permission, context=context)
        if not allowed:
            # Log forbidden access attempt to tamper-evident hash chain
            audit = SecurityAuditLogger.get_instance()
            audit.log_event(
                event_type="AUTH_FORBIDDEN_ACCESS",
                payload={
                    "user_id": user.get("user_id"),
                    "role": user.get("role"),
                    "attempted_permission": str(permission),
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{user.get('role')}' lacks permission '{permission}'.",
            )
        return user

    return dependency


async def authenticate_websocket(websocket: WebSocket) -> Optional[Dict[str, Any]]:
    """
    Authenticates WebSocket connections using the session cookie or query param.
    """
    token = websocket.cookies.get(COOKIE_NAME)
    if not token:
        token = websocket.query_params.get("token")
    if not token:
        return None
    return decode_session_jwt(token)
