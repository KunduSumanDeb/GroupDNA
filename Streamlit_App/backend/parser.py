"""WhatsApp chat parsing and validation utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable


TIMESTAMP_PATTERNS = (
    "%d/%m/%Y, %I:%M %p",
    "%d/%m/%y, %I:%M %p",
    "%m/%d/%Y, %I:%M %p",
    "%m/%d/%y, %I:%M %p",
    "%d/%m/%Y, %H:%M",
    "%d/%m/%y, %H:%M",
    "%m/%d/%Y, %H:%M",
    "%m/%d/%y, %H:%M",
)

MESSAGE_START = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s+(?P<time>\d{1,2}:\d{2}(?:\s?[\u202f ]?[APMapm]{2})?)\s+-\s+(?P<body>.*)$"
)


@dataclass
class ValidationReport:
    total_lines: int = 0
    merged_messages: int = 0
    valid_messages: int = 0
    invalid_lines: int = 0
    system_messages: int = 0
    media_messages: int = 0
    deleted_messages: int = 0
    malformed_timestamps: int = 0
    unknown_senders: int = 0
    duplicate_entries: int = 0
    corrupted_lines: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def normalize_timestamp(value: str) -> datetime | None:
    clean = (
        value.replace("\u202f", " ")
        .replace("\xa0", " ")
        .replace("am", "AM")
        .replace("pm", "PM")
        .strip()
    )
    clean = re.sub(r"\s+", " ", clean)
    for pattern in TIMESTAMP_PATTERNS:
        try:
            return datetime.strptime(clean, pattern)
        except ValueError:
            continue
    return None


def merge_multiline_messages(lines: Iterable[str], report: ValidationReport) -> list[str]:
    messages: list[str] = []
    current = ""

    for raw in lines:
        report.total_lines += 1
        line = raw.strip("\ufeff\r\n")
        if not line.strip():
            continue

        if MESSAGE_START.match(line):
            if current:
                messages.append(current)
            current = line.strip()
        elif current:
            current += " " + line.strip()
        else:
            report.invalid_lines += 1
            report.corrupted_lines += 1

    if current:
        messages.append(current)

    report.merged_messages = len(messages)
    return messages


def parse_chat_text(text: str) -> tuple[list[dict], ValidationReport]:
    report = ValidationReport()
    messages = merge_multiline_messages(text.splitlines(), report)
    parsed: list[dict] = []
    seen: set[tuple] = set()

    for raw in messages:
        match = MESSAGE_START.match(raw)
        if not match:
            report.invalid_lines += 1
            report.corrupted_lines += 1
            continue

        timestamp_text = f"{match.group('date')}, {match.group('time')}"
        timestamp = normalize_timestamp(timestamp_text)
        if timestamp is None:
            report.malformed_timestamps += 1
            report.errors.append(f"Could not parse timestamp: {timestamp_text}")
            continue

        body = match.group("body")
        if ": " not in body:
            report.system_messages += 1
            continue

        sender, message_text = body.split(": ", 1)
        sender = sender.strip()
        message_text = message_text.strip()

        if not sender:
            report.unknown_senders += 1
            continue

        lower_text = message_text.lower()
        is_media = message_text == "<Media omitted>" or "media omitted" in lower_text
        is_deleted = "message was deleted" in lower_text or "deleted this message" in lower_text

        if is_media:
            report.media_messages += 1
        if is_deleted:
            report.deleted_messages += 1

        key = (timestamp, sender, message_text)
        if key in seen:
            report.duplicate_entries += 1
        else:
            seen.add(key)

        parsed.append(
            {
                "timestamp": timestamp,
                "sender": sender,
                "text": message_text,
                "is_media": is_media,
                "is_deleted": is_deleted,
                "is_question": "?" in message_text,
                "is_caps": _is_caps_message(message_text),
                "is_weekend": timestamp.weekday() >= 5,
                "is_night": timestamp.hour < 5 or timestamp.hour >= 22,
            }
        )

    report.valid_messages = len(parsed)
    if not parsed:
        report.errors.append("No valid WhatsApp messages were found in the uploaded file.")
    return parsed, report


def _is_caps_message(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    if len(letters) < 4:
        return False
    uppercase = sum(1 for char in letters if char.isupper())
    return uppercase / len(letters) >= 0.75
