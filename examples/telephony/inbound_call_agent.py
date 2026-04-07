"""Complete inbound call example with caller identification, business hours routing,
and call summary generation.

This example demonstrates a production-ready inbound call bot that:
1. Extracts caller phone number and metadata from SIP
2. Routes based on business hours
3. Handles the conversation with tools
4. Generates a call summary on hangup
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, time

from dotenv import load_dotenv

from livekit import rtc

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RunContext,
    TurnHandlingOptions,
    cli,
    extract_caller_info,
    extract_caller_info_from_room,
    format_phone_number,
    inference,
    metrics,
    room_io,
)
from livekit.agents.llm import function_tool
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

logger = logging.getLogger("inbound-call-agent")


@dataclass
class CallData:
    """Shared state for the call session."""

    caller_phone: str | None = None
    caller_name: str | None = None
    call_start_time: datetime | None = None
    call_summary: str | None = None
    conversation_log: list[str] = field(default_factory=list)
    is_business_hours: bool = True
    voicemail_left: bool = False


def check_business_hours(
    tz_offset: int = 0,
    work_start: time = time(9, 0),
    work_end: time = time(17, 0),
    workdays: set[int] = None,
) -> bool:
    """Check if current time is within business hours.

    Args:
        tz_offset: UTC offset in hours (e.g., 8 for UTC+8).
        work_start: Business hours start time.
        work_end: Business hours end time.
        workdays: Set of work days (0=Monday, 6=Sunday). Defaults to Mon-Fri.

    Returns:
        True if within business hours.
    """
    if workdays is None:
        workdays = {0, 1, 2, 3, 4}

    now = datetime.utcnow()
    if tz_offset:
        from datetime import timedelta

        now = now + timedelta(hours=tz_offset)

    if now.weekday() not in workdays:
        return False

    current_time = now.time()
    return work_start <= current_time <= work_end


class GreetingAgent(Agent):
    """Greets the caller and routes based on business hours."""

    def __init__(self, call_data: CallData) -> None:
        super().__init__(
            instructions=(
                "You are a friendly receptionist for Acme Corporation. "
                "Keep responses concise and professional. "
                "Do not use emojis, asterisks, or markdown formatting. "
                "Speak naturally and conversationally."
            ),
        )
        self._call_data = call_data

    async def on_enter(self) -> None:
        caller_display = self._call_data.caller_name or self._call_data.caller_phone or "Caller"

        if self._call_data.is_business_hours:
            self.session.generate_reply(
                instructions=(
                    f"{caller_display} has called during business hours. "
                    "Greet them warmly by name if known, or generically. "
                    "Ask how you can help them today."
                )
            )
        else:
            self.session.generate_reply(
                instructions=(
                    f"{caller_display} has called outside business hours. "
                    "Apologize that the office is currently closed. "
                    "Offer to take a message or let them know business hours. "
                    "Ask if they'd like to leave a voicemail."
                )
            )


class MainAgent(Agent):
    """Handles the main conversation during business hours."""

    def __init__(self, call_data: CallData) -> None:
        super().__init__(
            instructions=(
                "You are a helpful customer service representative for Acme Corporation. "
                "Keep responses concise and professional. "
                "Do not use emojis, asterisks, or markdown formatting. "
                "If you cannot help the caller, offer to transfer them to a human agent."
            ),
        )
        self._call_data = call_data

    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions="Continue the conversation naturally based on the caller's needs."
        )

    @function_tool
    async def log_call_note(
        self,
        context: RunContext,
        note: str,
    ) -> str:
        """Record a note about this call for follow-up.

        Args:
            note: The note to record.
        """
        self._call_data.conversation_log.append(f"NOTE: {note}")
        logger.info(f"Call note logged: {note}")
        return "Note recorded successfully."

    @function_tool
    async def end_call(
        self,
        context: RunContext,
    ) -> str:
        """End the call politely when the conversation is complete."""
        self.session.generate_reply(
            instructions="Thank the caller warmly and end the conversation.",
            allow_interruptions=False,
        )
        import asyncio

        asyncio.create_task(self._end_session("call_completed"))
        return "Call ending..."

    async def _end_session(self, reason: str) -> None:
        """End the session after the farewell message has been played."""
        import asyncio

        await asyncio.sleep(3)
        self.session.shutdown()


class AfterHoursAgent(Agent):
    """Handles after-hours calls and voicemail."""

    def __init__(self, call_data: CallData) -> None:
        super().__init__(
            instructions=(
                "You are an after-hours message taker for Acme Corporation. "
                "Our business hours are Monday-Friday, 9am to 5pm. "
                "Collect the caller's name, phone number, and message. "
                "Confirm the details back to them before ending. "
                "Keep responses concise. No emojis or markdown."
            ),
        )
        self._call_data = call_data

    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions="Ask for the caller's name, phone number, and message."
        )

    @function_tool
    async def save_voicemail(
        self,
        context: RunContext,
        name: str,
        phone: str,
        message: str,
    ) -> str:
        """Save the voicemail after collecting all details.

        Args:
            name: Caller's name.
            phone: Caller's phone number.
            message: The voicemail message.
        """
        self._call_data.voicemail_left = True
        self._call_data.conversation_log.append(
            f"VOICEMAIL from {name} ({phone}): {message}"
        )
        logger.info(f"Voicemail saved from {name} at {phone}")
        return "Voicemail saved successfully."

    @function_tool
    async def end_call(
        self,
        context: RunContext,
    ) -> str:
        """End the call after voicemail is saved."""
        self.session.generate_reply(
            instructions="Thank the caller and let them know someone will return their call during business hours.",
            allow_interruptions=False,
        )
        import asyncio

        asyncio.create_task(self._end_session("voicemail_completed"))
        return "Call ending..."

    async def _end_session(self, reason: str) -> None:
        """End the session after the farewell message has been played."""
        import asyncio

        await asyncio.sleep(3)
        self.session.shutdown()


server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Extract caller information
    call_data = CallData(
        call_start_time=datetime.utcnow(),
    )

    # Wait briefly for SIP participant to connect
    import asyncio

    try:
        await asyncio.wait_for(ctx.wait_for_participant(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("No participant connected within timeout")

    # Extract caller info from room
    caller_info = extract_caller_info_from_room(ctx.room)
    if caller_info:
        call_data.caller_phone = caller_info.phone_number
        call_data.caller_name = caller_info.display_name
        logger.info(
            f"Inbound call from: {call_data.caller_name or call_data.caller_phone or 'Unknown'}"
        )

        # Log SIP headers if available
        from livekit.agents import get_sip_headers

        if caller_info.raw_attributes:
            # Find the SIP participant to extract headers
            for p in ctx.room.remote_participants.values():
                if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    sip_headers = get_sip_headers(p)
                    if sip_headers:
                        logger.info(f"SIP headers: {sip_headers}")
                    break

    # Check business hours (customize for your timezone)
    call_data.is_business_hours = check_business_hours(
        tz_offset=8,  # UTC+8, adjust as needed
        work_start=time(9, 0),
        work_end=time(17, 0),
    )

    # Create appropriate agent based on business hours
    if call_data.is_business_hours:
        agent = MainAgent(call_data)
    else:
        agent = AfterHoursAgent(call_data)

    session: AgentSession[CallData] = AgentSession(
        stt=inference.STT("deepgram/nova-3", language="multi"),
        llm=inference.LLM("openai/gpt-4.1-mini"),
        tts=inference.TTS("cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
            interruption={
                "resume_false_interruption": True,
                "false_interruption_timeout": 1.0,
            },
        ),
        preemptive_generation=True,
        userdata=call_data,
    )

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent) -> None:
        metrics.log_metrics(ev.metrics)

    @session.on("close")
    def _on_session_close(ev) -> None:
        # Generate call summary
        duration = datetime.utcnow() - call_data.call_start_time
        summary = (
            f"Call Summary\n"
            f"============\n"
            f"Caller: {call_data.caller_name or call_data.caller_phone or 'Unknown'}\n"
            f"Phone: {call_data.caller_phone or 'N/A'}\n"
            f"Duration: {duration.total_seconds():.0f} seconds\n"
            f"Business Hours: {call_data.is_business_hours}\n"
            f"Voicemail Left: {call_data.voicemail_left}\n"
            f"Notes: {'; '.join(call_data.conversation_log) if call_data.conversation_log else 'None'}\n"
        )
        call_data.call_summary = summary
        logger.info(f"\n{summary}")

    async def log_usage() -> None:
        logger.info(f"Usage: {session.usage}")
        if call_data.call_summary:
            logger.info(f"Final summary: {call_data.call_summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            close_on_disconnect=True,
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)
