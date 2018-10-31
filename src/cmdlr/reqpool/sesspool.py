"""Maintain aiohttp sessions."""

from aiohttp import ClientSession
from aiohttp import ClientTimeout


class SessionPool:
    """Maintain a aiohttp client session pool."""

    def __init__(self):
        """Session pool init."""
        self.sessions = []

    def build_session(self, analyzer_system):
        """Build a new session."""
        session_init_kwargs = {
            'timeout': ClientTimeout(total=analyzer_system['timeout']),
        }

        session = ClientSession(
            **session_init_kwargs,
        )

        self.sessions.append(session)

        return session

    async def close(self):
        """Close all dispatched sessions."""
        for session in self.sessions:
            await session.close()

        self.sessions.clear()
