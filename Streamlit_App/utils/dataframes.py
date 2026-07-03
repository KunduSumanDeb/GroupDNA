"""Conversion helpers for Streamlit and Plotly."""

from __future__ import annotations

import pandas as pd


def chat_dataframe(report: dict) -> pd.DataFrame:
    data = report.get("chat_data", [])
    frame = pd.DataFrame(data)
    if frame.empty:
        return frame
    frame["date"] = frame["timestamp"].dt.date
    frame["hour"] = frame["timestamp"].dt.hour
    frame["weekday"] = frame["timestamp"].dt.day_name()
    frame["month"] = frame["timestamp"].dt.to_period("M").astype(str)
    frame["year"] = frame["timestamp"].dt.year
    frame["length"] = frame["text"].astype(str).str.len()
    return frame


def leaderboard_dataframe(report: dict) -> pd.DataFrame:
    rows = report.get("group_overview", {}).get("leaderboard", [])
    return pd.DataFrame(rows, columns=["member", "messages"])


def top_words_dataframe(report: dict, limit: int = 50) -> pd.DataFrame:
    rows = report.get("word_statistics", {}).get("top_words", [])[:limit]
    return pd.DataFrame(rows, columns=["word", "count"])


def response_dataframe(report: dict) -> pd.DataFrame:
    values = report.get("response_analysis", {}).get("average_response_time", {})
    return pd.DataFrame(values.items(), columns=["member", "avg_response_minutes"])


def archetype_dataframe(report: dict) -> pd.DataFrame:
    assignments = report.get("personality_archetypes", {})
    rows = []
    for member, details in assignments.items():
        rows.append(
            {
                "member": member,
                "archetype": details.get("Archetype"),
                "score": details.get("Score", 0),
                "confidence": details.get("Confidence", 0),
                "runner_up": details.get("RunnerUp"),
            }
        )
    return pd.DataFrame(rows)
