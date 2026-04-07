"""Utilities for extracting caller information from inbound SIP calls.

This module provides helpers to extract caller phone numbers (ANI/CLI),
SIP headers, and other telephony metadata from LiveKit SIP participants.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from livekit import rtc

if TYPE_CHECKING:
    from livekit import api

logger = logging.getLogger(__name__)


@dataclass
class CallerInfo:
    """Extracted information about an inbound SIP caller.

    Attributes:
        phone_number: The caller's phone number (ANI/CLI), normalized if possible.
        display_name: The caller's display name from SIP From header.
        sip_from: Raw SIP From URI (e.g. "sip:+15105550123@carrier.com").
        sip_to: Raw SIP To URI (the dialed number/destination).
        sip_call_id: Unique SIP Call-ID header value.
        sip_trunk_id: The SIP trunk that received this call.
        participant_identity: The LiveKit participant identity for this caller.
        participant_name: The display name set on the LiveKit participant.
        raw_attributes: All raw participant attributes for custom SIP headers.
        raw_metadata: The participant metadata string.
    """

    phone_number: str | None = None
    display_name: str | None = None
    sip_from: str | None = None
    sip_to: str | None = None
    sip_call_id: str | None = None
    sip_trunk_id: str | None = None
    participant_identity: str = ""
    participant_name: str = ""
    raw_attributes: dict[str, str] = field(default_factory=dict)
    raw_metadata: str = ""

    @property
    def is_sip_call(self) -> bool:
        """Whether this caller appears to be a SIP participant."""
        return self.sip_from is not None or self.sip_call_id is not None

    @property
    def formatted_phone(self) -> str:
        """Return a human-friendly formatted phone number, or fallback."""
        if self.phone_number:
            return format_phone_number(self.phone_number)
        return self.display_name or self.participant_name or self.participant_identity or "Unknown"


def extract_caller_info(
    participant: rtc.RemoteParticipant,
) -> CallerInfo:
    """Extract caller information from a SIP participant's attributes and metadata.

    LiveKit populates participant attributes with SIP metadata when a SIP
    participant joins a room. This helper extracts the relevant fields.

    Args:
        participant: The RemoteParticipant representing the inbound caller.

    Returns:
        CallerInfo with all extractable caller details.
    """
    attrs = dict(participant.attributes)
    info = CallerInfo(
        participant_identity=participant.identity,
        participant_name=participant.name,
        raw_attributes=attrs,
        raw_metadata=participant.metadata,
    )

    # Phone number: check common attribute keys used by LiveKit SIP
    for key in (
        "sip.caller_number",
        "sip.caller",
        "sip.from_user",
        "sip.phone_number",
        "caller_number",
        "phone_number",
        "ani",
    ):
        val = attrs.get(key)
        if val:
            info.phone_number = val
            break

    # Display name
    for key in ("sip.caller_name", "caller_name", "display_name", "sip.from_name"):
        val = attrs.get(key)
        if val:
            info.display_name = val
            break

    # SIP From / To URIs
    info.sip_from = attrs.get("sip.from_uri") or attrs.get("sip_from")
    info.sip_to = attrs.get("sip.to_uri") or attrs.get("sip_to")

    # SIP Call-ID
    info.sip_call_id = attrs.get("sip.call_id") or attrs.get("sip_call_id")

    # SIP Trunk ID
    info.sip_trunk_id = attrs.get("sip.trunk_id") or attrs.get("sip_trunk_id")

    # If phone number not found in attributes, try parsing from SIP From URI
    if not info.phone_number and info.sip_from:
        info.phone_number = _extract_phone_from_sip_uri(info.sip_from)

    # Fallback: try participant metadata (JSON or custom format)
    if not info.phone_number and info.raw_metadata:
        info.phone_number = _extract_phone_from_metadata(info.raw_metadata)

    logger.info(
        "Extracted caller info: phone=%s, name=%s, identity=%s",
        info.phone_number,
        info.display_name,
        info.participant_identity,
    )
    return info


def extract_caller_info_from_room(room: rtc.Room) -> CallerInfo | None:
    """Find the SIP caller in a room and extract their info.

    Scans all remote participants for the first SIP participant and extracts
    caller information.

    Args:
        room: The LiveKit room to scan.

    Returns:
        CallerInfo if a SIP participant is found, else None.
    """
    for identity, participant in room.remote_participants.items():
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            return extract_caller_info(participant)

    # Fallback: check attributes for SIP indicators
    for identity, participant in room.remote_participants.items():
        attrs = dict(participant.attributes)
        if any(k.startswith("sip.") for k in attrs):
            return extract_caller_info(participant)

    return None


def get_sip_headers(participant: rtc.RemoteParticipant) -> dict[str, str]:
    """Extract custom SIP headers from participant attributes.

    LiveKit stores custom SIP headers with keys prefixed by "sip.header.".

    Args:
        participant: The SIP participant.

    Returns:
        Dictionary of SIP header name -> value.
    """
    headers: dict[str, str] = {}
    prefix = "sip.header."
    for key, value in participant.attributes.items():
        if key.startswith(prefix):
            header_name = key[len(prefix) :]
            headers[header_name] = value
    return headers


def get_sip_header(
    participant: rtc.RemoteParticipant,
    header_name: str,
    default: str | None = None,
) -> str | None:
    """Get a specific custom SIP header value.

    Args:
        participant: The SIP participant.
        header_name: The SIP header name (case-insensitive).
        default: Default value if header not found.

    Returns:
        The header value or default.
    """
    headers = get_sip_headers(participant)
    header_name_lower = header_name.lower()
    for name, value in headers.items():
        if name.lower() == header_name_lower:
            return value
    return default


def normalize_phone_number(phone: str) -> str:
    """Normalize a phone number to E.164 format if possible.

    Strips non-digit characters except leading +.
    If the number starts with +, keeps it. Otherwise adds + for numbers
    that look like they could be E.164 (10+ digits).

    Args:
        phone: Raw phone number string.

    Returns:
        Normalized phone number string.
    """
    cleaned = re.sub(r"[^\d+]", "", phone)
    if cleaned.startswith("+"):
        return cleaned
    if len(cleaned) >= 10:
        return "+" + cleaned
    return cleaned


def format_phone_number(phone: str) -> str:
    """Format a phone number for human-readable display.

    Formats US numbers as (XXX) XXX-XXXX. Other numbers are returned
    with spaces every 3-4 digits for readability.

    Args:
        phone: Phone number string (may include + prefix).

    Returns:
        Formatted phone number string.
    """
    digits = re.sub(r"\D", "", phone)
    prefix = "+" if phone.startswith("+") else ""

    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    if len(digits) == 10:
        return f"{prefix}({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    # Generic formatting: group digits
    if len(digits) > 7:
        groups = []
        i = 0
        while i < len(digits):
            chunk_size = 4 if len(digits) - i >= 4 else 3
            groups.append(digits[i : i + chunk_size])
            i += chunk_size
        return f"{prefix}{' '.join(groups)}"

    return phone


def _extract_phone_from_sip_uri(uri: str) -> str | None:
    """Extract phone number from a SIP URI like sip:+15105550123@domain.com."""
    match = re.match(r"sip:(\+?\d+)@", uri)
    if match:
        return match.group(1)
    match = re.match(r"sip:(\d+)", uri)
    if match:
        return match.group(1)
    return None


def _extract_phone_from_metadata(metadata: str) -> str | None:
    """Try to extract phone number from participant metadata string.

    Handles JSON-like patterns and simple key=value formats.

    Args:
        metadata: Raw metadata string.

    Returns:
        Phone number if found, else None.
    """
    patterns = [
        r'"phone_number"\s*:\s*"([^"]+)"',
        r'"caller_number"\s*:\s*"([^"]+)"',
        r'"phone"\s*:\s*"([^"]+)"',
        r"phone_number=([^\s,}]+)",
        r"caller=([^\s,}]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, metadata)
        if match:
            return match.group(1)
    return None
