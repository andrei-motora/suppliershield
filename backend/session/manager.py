"""
Session lifecycle management for SupplierShield.

Manages per-session SupplierShieldEngine instances with TTL-based
expiration and LRU eviction.
"""

import logging
import secrets
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionMeta:
    """Metadata for a single session."""
    created_at: float
    last_accessed: float
    expires_at: float
    status: str = "active"  # active, processing, expired


class SessionManager:
    """Manages per-session analytics engines with TTL and capacity limits."""

    def __init__(
        self,
        base_dir: Optional[str] = None,
        max_sessions: int = 100,
        ttl_seconds: int = 7200,
    ):
        self.base_dir = Path(base_dir or self._default_base_dir())
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds

        self._engines: Dict[str, object] = {}  # session_id -> SupplierShieldEngine
        self._metadata: Dict[str, SessionMeta] = {}
        self._lock = threading.RLock()
        self._build_semaphore = threading.Semaphore(5)

        # Start background cleanup timer
        self._cleanup_timer: Optional[threading.Timer] = None
        self._running = True
        self._schedule_cleanup()

        logger.info(
            "SessionManager initialized: base_dir=%s, max=%d, ttl=%ds",
            self.base_dir, max_sessions, ttl_seconds,
        )

    @staticmethod
    def _default_base_dir() -> str:
        import tempfile
        return str(Path(tempfile.gettempdir()) / "suppliershield" / "sessions")

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        with self._lock:
            self._enforce_capacity()
            session_id = secrets.token_urlsafe(32)
            now = time.time()
            self._metadata[session_id] = SessionMeta(
                created_at=now,
                last_accessed=now,
                expires_at=now + self.ttl_seconds,
            )
            # Create session directory
            session_dir = self.base_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created session %s…", session_id[:8])
            return session_id

    def get_engine(self, session_id: str):
        """Return the engine for a session, or None if not found. Extends TTL on access."""
        with self._lock:
            meta = self._metadata.get(session_id)
            if meta is None:
                return None
            if time.time() > meta.expires_at:
                self._destroy_session_unlocked(session_id)
                return None
            meta.last_accessed = time.time()
            meta.expires_at = meta.last_accessed + self.ttl_seconds
            return self._engines.get(session_id)

    def set_engine(self, session_id: str, engine) -> None:
        """Store an engine for a session."""
        with self._lock:
            meta = self._metadata.get(session_id)
            if meta is None:
                raise ValueError(f"Session {session_id[:8]}… does not exist")
            self._engines[session_id] = engine
            meta.last_accessed = time.time()
            meta.expires_at = meta.last_accessed + self.ttl_seconds
            meta.status = "active"
            logger.info("Engine stored for session %s…", session_id[:8])

    def has_session(self, session_id: str) -> bool:
        """Check if a session exists and is not expired."""
        with self._lock:
            meta = self._metadata.get(session_id)
            if meta is None:
                return False
            if time.time() > meta.expires_at:
                self._destroy_session_unlocked(session_id)
                return False
            return True

    def get_session_dir(self, session_id: str) -> Path:
        """Return the temp directory for a session. Validates path safety."""
        # Validate session_id format (base64url characters only)
        safe_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        if not all(c in safe_chars for c in session_id):
            raise ValueError("Invalid session ID format")
        session_dir = (self.base_dir / session_id).resolve()
        # Path traversal prevention
        if not str(session_dir).startswith(str(self.base_dir.resolve())):
            raise ValueError("Invalid session path")
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def destroy_session(self, session_id: str) -> None:
        """Remove a session, its engine, and its temp files."""
        with self._lock:
            self._destroy_session_unlocked(session_id)

    def _destroy_session_unlocked(self, session_id: str) -> None:
        """Internal destroy (caller must hold lock)."""
        self._engines.pop(session_id, None)
        self._metadata.pop(session_id, None)
        session_dir = self.base_dir / session_id
        if session_dir.exists():
            try:
                shutil.rmtree(session_dir)
            except OSError:
                logger.warning("Failed to clean up session dir %s", session_id[:8])
        logger.info("Destroyed session %s…", session_id[:8])

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        with self._lock:
            now = time.time()
            expired = [
                sid for sid, meta in self._metadata.items()
                if now > meta.expires_at
            ]
            for sid in expired:
                self._destroy_session_unlocked(sid)
            if expired:
                logger.info("Cleaned up %d expired sessions", len(expired))
            return len(expired)

    def _enforce_capacity(self) -> None:
        """Evict oldest sessions if at capacity (caller must hold lock)."""
        while len(self._metadata) >= self.max_sessions:
            # LRU: evict session with oldest last_accessed
            oldest = min(self._metadata.items(), key=lambda x: x[1].last_accessed)
            logger.info("Evicting LRU session %s…", oldest[0][:8])
            self._destroy_session_unlocked(oldest[0])

    def _schedule_cleanup(self) -> None:
        """Schedule the next cleanup run."""
        if not self._running:
            return
        self._cleanup_timer = threading.Timer(60.0, self._run_cleanup)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _run_cleanup(self) -> None:
        """Periodic cleanup callback."""
        try:
            self.cleanup_expired()
        except Exception:
            logger.exception("Error during session cleanup")
        finally:
            self._schedule_cleanup()

    def shutdown(self) -> None:
        """Stop background cleanup. Call during app shutdown."""
        self._running = False
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
        logger.info("SessionManager shutdown")

    @property
    def active_session_count(self) -> int:
        with self._lock:
            return len(self._metadata)

    def acquire_build_semaphore(self) -> bool:
        """Acquire semaphore for engine builds. Returns True if acquired."""
        return self._build_semaphore.acquire(timeout=0)

    def release_build_semaphore(self) -> None:
        """Release engine build semaphore."""
        self._build_semaphore.release()
