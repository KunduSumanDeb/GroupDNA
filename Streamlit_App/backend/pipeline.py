"""Pipeline entry points used by the Streamlit app."""

from __future__ import annotations

import pickle
from pathlib import Path

from .analytics import calculate_report
from .parser import parse_chat_text


APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "Data"


def analyze_chat(text: str) -> dict:
    chat_data, validation = parse_chat_text(text)
    return calculate_report(chat_data, validation.as_dict())


def load_demo_report() -> dict:
    final_report = DATA_DIR / "final_report.pkl"
    parsed_chat = DATA_DIR / "parsed_chat.pkl"
    if final_report.exists():
        with final_report.open("rb") as handle:
            report = pickle.load(handle)
        if "chat_data" not in report and parsed_chat.exists():
            with parsed_chat.open("rb") as handle:
                report["chat_data"] = pickle.load(handle)
        return _normalize_legacy_report(report)
    if parsed_chat.exists():
        with parsed_chat.open("rb") as handle:
            chat_data = pickle.load(handle)
        _enrich_legacy_messages(chat_data)
        return calculate_report(chat_data, {"demo_data": True})
    return calculate_report([], {"errors": ["No demo data found."]})


def _normalize_legacy_report(report: dict) -> dict:
    chat_data = report.get("chat_data", [])
    if chat_data:
        _enrich_legacy_messages(chat_data)
        enriched = calculate_report(chat_data, {"demo_data": True})
        for key, value in report.items():
            if key not in enriched:
                enriched[key] = value
        return enriched
    return report


def _enrich_legacy_messages(chat_data: list[dict]) -> None:
    for message in chat_data:
        text = message.get("text", "")
        message["is_media"] = text == "<Media omitted>" or "media omitted" in text.lower()
        message["is_deleted"] = "message was deleted" in text.lower() or "deleted this message" in text.lower()
        message["is_question"] = "?" in text
        letters = [char for char in text if char.isalpha()]
        message["is_caps"] = len(letters) >= 4 and sum(1 for char in letters if char.isupper()) / len(letters) >= 0.75
        message["is_weekend"] = message["timestamp"].weekday() >= 5
        message["is_night"] = message["timestamp"].hour < 5 or message["timestamp"].hour >= 22
