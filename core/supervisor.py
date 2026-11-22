import time

from astrbot.api import logger

from .config import PluginConfig


class SupervisorManager:
    """Manage persistent and expiring supervisor entries."""

    def __init__(self, config: PluginConfig):
        self.config = config
        self._supervisors: dict[str, int | None] = {}
        for user_id in config.user_ids:
            self._supervisors[str(user_id)] = None

    def cleanup_expired(self) -> None:
        """Remove expired runtime supervisor entries."""
        now = int(time.time())
        expired = [
            user_id
            for user_id, expires_at in self._supervisors.items()
            if expires_at is not None and expires_at <= now
        ]
        for user_id in expired:
            self._supervisors.pop(user_id, None)
        if expired:
            logger.debug(f"Cleaned up expired supervisor entries: {expired}")

    def is_supervising(self, user_id: str) -> bool:
        """Check whether a user is currently supervised.

        Args:
            user_id: User ID to inspect.

        Returns:
            Whether the user has a persistent or unexpired entry.
        """
        self.cleanup_expired()
        return user_id in self._supervisors

    def add_supervisors(self, user_ids: list[str], minute: int | None = None) -> int:
        """Add runtime supervisor entries with a bounded duration.

        Args:
            user_ids: User IDs to supervise.
            minute: Requested duration in minutes, or ``None`` for the default.

        Returns:
            The effective duration in minutes.
        """
        requested_second = self.config.default_second if minute is None else minute * 60
        duration_second = min(
            self.config.max_second,
            max(60, requested_second),
        )
        expires_at = int(time.time()) + duration_second
        for user_id in user_ids:
            self._supervisors[user_id] = expires_at
        return duration_second // 60

    def remove_supervisors(self, user_ids: list[str]) -> None:
        """Remove supervisor entries.

        Args:
            user_ids: User IDs to remove.
        """
        for user_id in user_ids:
            self._supervisors.pop(user_id, None)

    def list_supervisors(self) -> dict[str, int | None]:
        """Return active entries and remaining whole minutes.

        Returns:
            A mapping from user ID to remaining minutes. ``None`` denotes a
            persistent entry loaded from configuration.
        """
        self.cleanup_expired()
        now = int(time.time())
        return {
            user_id: (
                None if expires_at is None else max(0, (expires_at - now + 59) // 60)
            )
            for user_id, expires_at in self._supervisors.items()
        }
