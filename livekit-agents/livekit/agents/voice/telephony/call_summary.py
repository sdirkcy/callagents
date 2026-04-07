"""Call summary generation utilities.

Provides automatic call summary generation at the end of each call,
including conversation transcription, key topics, and action items.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from livekit.agents import llm

if TYPE_CHECKING:
    from livekit.agents import AgentSession

logger = logging.getLogger(__name__)


@dataclass
class CallSummary:
    """Generated summary of a completed call.

    Attributes:
        caller_phone: Caller's phone number.
        caller_name: Caller's name.
        start_time: When the call started.
        end_time: When the call ended.
        duration_seconds: Total call duration.
        conversation_summary: Brief summary of what the call was about.
        key_topics: List of key topics discussed.
        action_items: Action items identified from the call.
        agent_name: Name/identifier of the agent that handled the call.
        resolution: How the call ended (completed, transferred, voicemail, etc.).
    """

    caller_phone: str | None = None
    caller_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_seconds: float = 0.0
    conversation_summary: str = ""
    key_topics: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    agent_name: str = ""
    resolution: str = "unknown"

    def to_text(self) -> str:
        """Convert to human-readable text format."""
        lines = [
            "=" * 50,
            "CALL SUMMARY",
            "=" * 50,
            f"Caller: {self.caller_name or self.caller_phone or 'Unknown'}",
            f"Phone: {self.caller_phone or 'N/A'}",
            f"Duration: {self._format_duration()}",
            f"Agent: {self.agent_name or 'N/A'}",
            f"Resolution: {self.resolution}",
            "",
            "Summary:",
            self.conversation_summary or "No summary available",
            "",
        ]

        if self.key_topics:
            lines.append("Key Topics:")
            for topic in self.key_topics:
                lines.append(f"  - {topic}")
            lines.append("")

        if self.action_items:
            lines.append("Action Items:")
            for item in self.action_items:
                lines.append(f"  - {item}")
            lines.append("")

        lines.append("=" * 50)
        return "\n".join(lines)

    def _format_duration(self) -> str:
        minutes = int(self.duration_seconds // 60)
        seconds = int(self.duration_seconds % 60)
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "caller_phone": self.caller_phone,
            "caller_name": self.caller_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "conversation_summary": self.conversation_summary,
            "key_topics": self.key_topics,
            "action_items": self.action_items,
            "agent_name": self.agent_name,
            "resolution": self.resolution,
        }


async def generate_call_summary(
    session: AgentSession,
    llm_client: llm.LLM,
    caller_phone: str | None = None,
    caller_name: str | None = None,
    agent_name: str = "",
) -> CallSummary:
    """Generate a call summary from the conversation history.

    Args:
        session: The agent session that just completed.
        llm_client: LLM to use for summary generation.
        caller_phone: Caller's phone number.
        caller_name: Caller's name.
        agent_name: Agent identifier.

    Returns:
        CallSummary with generated details.
    """
    chat_ctx = session.chat_ctx
    messages = list(chat_ctx.messages())

    conversation_parts = []
    for msg in messages:
        if msg.role in ("user", "assistant") and msg.text_content:
            role = "Caller" if msg.role == "user" else "Agent"
            conversation_parts.append(f"{role}: {msg.text_content}")

    conversation_text = (
        "\n".join(conversation_parts)
        if conversation_parts
        else "No conversation recorded."
    )

    summary_prompt = (
        "You are a call summary generator. Analyze the following phone call conversation\n"
        "and produce a structured summary.\n\n"
        f"CONVERSATION:\n{conversation_text}\n\n"
        "Based on this conversation, provide:\n"
        '1. A 2-3 sentence summary of what the call was about\n'
        '2. A list of key topics discussed (as a JSON array of strings)\n'
        '3. A list of action items or follow-ups needed (as a JSON array of strings)\n'
        '4. How the call ended: "completed", "transferred", "voicemail", "abandoned", or "other"\n\n'
        "Return ONLY valid JSON in this exact format:\n"
        '{\n'
        '    "summary": "...",\n'
        '    "topics": ["...", "..."],\n'
        '    "action_items": ["...", "..."],\n'
        '    "resolution": "..."\n'
        "}"
    )

    try:
        request_ctx = llm.ChatContext().append(
            role="user",
            text_content=summary_prompt,
        )

        stream = llm_client.chat(chat_ctx=request_ctx)
        full_text = ""
        async for chunk in stream:
            if chunk.delta and chunk.delta.content:
                full_text += chunk.delta.content

        json_start = full_text.find("{")
        json_end = full_text.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_text = full_text[json_start:json_end]
            data = json.loads(json_text)

            summary = CallSummary(
                caller_phone=caller_phone,
                caller_name=caller_name,
                conversation_summary=data.get("summary", ""),
                key_topics=data.get("topics", []),
                action_items=data.get("action_items", []),
                resolution=data.get("resolution", "unknown"),
                agent_name=agent_name,
            )
        else:
            summary = CallSummary(
                caller_phone=caller_phone,
                caller_name=caller_name,
                conversation_summary=(
                    full_text[:200] if full_text else "Summary generation failed"
                ),
                resolution="unknown",
                agent_name=agent_name,
            )

    except Exception as e:
        logger.warning("Failed to generate LLM summary: %s", e)
        summary = CallSummary(
            caller_phone=caller_phone,
            caller_name=caller_name,
            conversation_summary="Summary generation failed",
            resolution="error",
            agent_name=agent_name,
        )

    return summary


def create_simple_summary(
    caller_phone: str | None = None,
    caller_name: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    resolution: str = "unknown",
) -> CallSummary:
    """Create a simple call summary without LLM generation.

    Useful when LLM is not available or call was very short.

    Args:
        caller_phone: Caller's phone number.
        caller_name: Caller's name.
        start_time: Call start time.
        end_time: Call end time.
        resolution: How the call ended.

    Returns:
        CallSummary with basic information.
    """
    duration = 0.0
    if start_time and end_time:
        duration = (end_time - start_time).total_seconds()

    return CallSummary(
        caller_phone=caller_phone,
        caller_name=caller_name,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        conversation_summary=f"Call with {caller_name or caller_phone or 'unknown caller'}",
        resolution=resolution,
    )
