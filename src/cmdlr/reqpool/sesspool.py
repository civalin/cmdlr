"""Maintain aiohttp sessions."""

from aiohttp import ClientSession
from aiohttp import ClientTimeout

from .. import info


class SessionPool:
    """Maintain a aiohttp client session pool."""

    default_session_init_kwargs = {
        'headers': {
            'user-agent': '{}/{}'.format(info.PROJECT_NAME, info.VERSION)
        },
        'timeout': ClientTimeout(total=120),
    }

    def __init__(self, loop):
        """Session pool init."""
        self.loop = loop

        self.sessions = []

    def build_session(self, session_init_kwargs):
        """Build a new session."""
        real_session_init_kwargs = {
            **self.default_session_init_kwargs,
            **session_init_kwargs,
        }
        session = ClientSession(
            loop=self.loop,
            **real_session_init_kwargs,
        )

        self.sessions.append(session)

        return session

    async def close(self):
        """Close all dispatched sessions."""
        for session in self.sessions:
            await session.close()

        self.sessions.clear()
