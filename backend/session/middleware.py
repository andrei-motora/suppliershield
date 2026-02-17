"""
Session middleware for SupplierShield.

Reads/writes a signed session cookie and attaches the session ID
to request.state for downstream dependencies.
"""

import logging
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

COOKIE_NAME = "ss_session"
EXEMPT_PATHS = {"/api/health"}


class SessionMiddleware(BaseHTTPMiddleware):
    """Manages signed session cookies and ties them to SessionManager."""

    def __init__(self, app, secret_key: str, max_age: int = 7200):
        super().__init__(app)
        self.serializer = URLSafeTimedSerializer(secret_key)
        self.max_age = max_age

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip session handling for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        session_manager = request.app.state.session_manager
        session_id = None
        needs_cookie = False

        # Try to read existing session from cookie
        cookie_value = request.cookies.get(COOKIE_NAME)
        if cookie_value:
            try:
                session_id = self.serializer.loads(cookie_value, max_age=self.max_age)
                if not session_manager.has_session(session_id):
                    # Session expired on server side — create new
                    session_id = None
            except (BadSignature, SignatureExpired):
                session_id = None

        # Create new session if needed
        if session_id is None:
            session_id = session_manager.create_session()
            needs_cookie = True

        # Attach to request state
        request.state.session_id = session_id

        # Process request
        response = await call_next(request)

        # Set cookie if new session was created
        if needs_cookie:
            signed = self.serializer.dumps(session_id)
            response.set_cookie(
                key=COOKIE_NAME,
                value=signed,
                max_age=self.max_age,
                httponly=True,
                samesite="lax",
                path="/",
            )

        return response
