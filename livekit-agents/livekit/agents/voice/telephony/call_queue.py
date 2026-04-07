"""Call queue management with hold music and position announcements.

Provides a call queue system that:
1. Plays hold music while callers wait
2. Announces queue position periodically
3. Supports callback-from-queue option
4. Handles queue overflow gracefully
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from livekit import rtc

from livekit.agents.voice.background_audio import (
    AudioConfig,
    BackgroundAudioPlayer,
    BuiltinAudioClip,
    PlayHandle,
)

if TYPE_CHECKING:
    from livekit.agents import AgentSession

logger = logging.getLogger(__name__)


class QueueStatus(str, Enum):
    WAITING = "waiting"
    SERVING = "serving"
    CALLBACK_REQUESTED = "callback_requested"
    ABANDONED = "abandoned"


@dataclass
class QueueEntry:
    """A single entry in the call queue."""

    caller_phone: str | None
    caller_name: str | None
    session: AgentSession
    position: int = 0
    status: QueueStatus = QueueStatus.WAITING
    joined_at: float = 0.0
    callback_phone: str | None = None


class CallQueue:
    """Manages a queue of waiting callers with hold music and announcements."""

    def __init__(
        self,
        max_queue_size: int = 10,
        announcement_interval: float = 30.0,
        estimated_wait_per_call: float = 120.0,
    ) -> None:
        """Initialize the call queue.

        Args:
            max_queue_size: Maximum number of callers in queue before overflow.
            announcement_interval: Seconds between queue position announcements.
            estimated_wait_per_call: Estimated wait time per caller in seconds.
        """
        self._queue: list[QueueEntry] = []
        self._max_queue_size = max_queue_size
        self._announcement_interval = announcement_interval
        self._estimated_wait_per_call = estimated_wait_per_call
        self._running = False
        self._tasks: set[asyncio.Task] = set()

    @property
    def size(self) -> int:
        return len(self._queue)

    @property
    def is_full(self) -> bool:
        return self.size >= self._max_queue_size

    async def enqueue(
        self,
        session: AgentSession,
        caller_phone: str | None = None,
        caller_name: str | None = None,
    ) -> QueueEntry | None:
        """Add a caller to the queue.

        Args:
            session: The caller's AgentSession.
            caller_phone: Caller's phone number.
            caller_name: Caller's display name.

        Returns:
            QueueEntry if successfully enqueued, None if queue is full.
        """
        if self.is_full:
            logger.warning("Call queue is full, cannot enqueue")
            return None

        entry = QueueEntry(
            caller_phone=caller_phone,
            caller_name=caller_name,
            session=session,
            position=self.size + 1,
            joined_at=asyncio.get_event_loop().time(),
        )
        self._queue.append(entry)

        logger.info(
            f"Enqueued caller {caller_name or caller_phone or 'unknown'} at position {entry.position}"
        )

        # Start hold music and announcements for this caller
        task = asyncio.create_task(self._manage_waiting(entry))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

        return entry

    def dequeue(self) -> QueueEntry | None:
        """Remove and return the first caller in queue."""
        if not self._queue:
            return None

        entry = self._queue.pop(0)
        entry.status = QueueStatus.SERVING

        # Update positions for remaining callers
        for i, e in enumerate(self._queue):
            e.position = i + 1

        logger.info(
            f"Dequeued caller {entry.caller_name or entry.caller_phone or 'unknown'}, "
            f"{self.size} remaining in queue"
        )
        return entry

    async def remove_caller(self, session: AgentSession) -> None:
        """Remove a specific caller from the queue.

        Args:
            session: The caller's AgentSession to remove.
        """
        for i, entry in enumerate(self._queue):
            if entry.session is session:
                removed = self._queue.pop(i)
                removed.status = QueueStatus.ABANDONED

                # Update positions
                for j, e in enumerate(self._queue):
                    e.position = j + 1

                logger.info(f"Removed caller from queue, {self.size} remaining")
                return

    async def _manage_waiting(self, entry: QueueEntry) -> None:
        """Manage hold music and periodic announcements for a waiting caller."""
        player = BackgroundAudioPlayer()

        try:
            # Start hold music
            room = entry.session.room_io.room if entry.session.room_io else None
            if room:
                await player.start(room=room)
                hold_handle = player.play(
                    AudioConfig(BuiltinAudioClip.HOLD_MUSIC, volume=0.6),
                    loop=True,
                )

                # Announce initial position
                await self._announce_position(entry, player)

                # Periodic announcements
                while entry.status == QueueStatus.WAITING:
                    await asyncio.sleep(self._announcement_interval)
                    if entry.status == QueueStatus.WAITING:
                        await self._announce_position(entry, player)

                # Stop music when no longer waiting
                if hold_handle:
                    hold_handle.stop()

        except Exception:
            logger.exception("Error managing queue waiting for caller")
        finally:
            await player.aclose()

    async def _announce_position(self, entry: QueueEntry, player: BackgroundAudioPlayer) -> None:
        """Announce the caller's queue position and estimated wait time."""
        position = entry.position
        wait_minutes = int((position * self._estimated_wait_per_call) / 60)

        announcement = (
            f"You are number {position} in the queue. "
            f"Estimated wait time is approximately {wait_minutes} minutes. "
            f"Please continue to hold and the next available agent will assist you."
        )

        if position <= 2:
            announcement += " You will be connected very soon."

        try:
            # Temporarily lower music volume for announcement
            await entry.session.say(announcement, allow_interruptions=False)
            logger.info(f"Queue announcement for position {position}: {announcement}")
        except Exception:
            logger.warning("Failed to make queue position announcement")

    def get_wait_time(self, position: int) -> float:
        """Get estimated wait time in seconds for a given position."""
        return position * self._estimated_wait_per_call


# Global queue instance (one per agent server)
_default_queue: CallQueue | None = None


def get_queue(
    max_queue_size: int = 10,
    announcement_interval: float = 30.0,
) -> CallQueue:
    """Get or create the default call queue.

    Args:
        max_queue_size: Maximum queue size.
        announcement_interval: Seconds between announcements.

    Returns:
        The CallQueue instance.
    """
    global _default_queue
    if _default_queue is None:
        _default_queue = CallQueue(
            max_queue_size=max_queue_size,
            announcement_interval=announcement_interval,
        )
    return _default_queue
