"""Streamlit UI helpers."""

from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st


def load_css() -> None:
    css_path = Path(__file__).resolve().parents[1] / "styles" / "app.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def metric_card(label: str, value, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="gdna-card gdna-metric">
            <div class="gdna-metric-label">{html.escape(str(label))}</div>
            <div class="gdna-metric-value">{html.escape(format_value(value))}</div>
            <div class="gdna-metric-caption">{html.escape(str(caption))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <section class="gdna-hero">
            <div class="gdna-pill">WhatsApp Analytics Replay</div>
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="gdna-page-title">
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(caption)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_value(value) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def download_button(label: str, data: bytes | str, file_name: str, mime: str) -> None:
    st.download_button(label=label, data=data, file_name=file_name, mime=mime, use_container_width=True)


def has_report() -> bool:
    return "report" in st.session_state and bool(st.session_state["report"].get("chat_data"))


def empty_state(message: str = "Upload a WhatsApp .txt export to unlock this page.") -> None:
    st.info(message)
