from __future__ import annotations

import sqlite3
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from backend import analyze_chat, load_demo_report
from config import (
    APP_NAME,
    APP_SUBTITLE,
    CHART_TEMPLATE_DARK,
    CHART_TEMPLATE_LIGHT,
    DEFAULT_UPLOAD_SIZE_MB,
    SIDEBAR_PAGES,
    UPLOAD_SIZE_OPTIONS_MB,
    VERSION,
)
from exports.reporting import chat_to_csv, chat_to_excel, report_to_html, report_to_json, report_to_pdf_bytes
from utils.dataframes import archetype_dataframe, chat_dataframe, leaderboard_dataframe, response_dataframe, top_words_dataframe
from utils.ui import empty_state, has_report, hero, load_css, metric_card, page_title
from visualizations import charts


ROOT = Path(__file__).resolve().parent
FEEDBACK_DB = ROOT / "data" / "feedback.sqlite3"


st.set_page_config(
    page_title=f"{APP_NAME} | {APP_SUBTITLE}",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": f"{APP_NAME} {VERSION}"},
)
load_css()


@st.cache_data(show_spinner=False)
def cached_analyze_chat(text: str) -> dict:
    return analyze_chat(text)


@st.cache_data(show_spinner=False)
def cached_demo_report() -> dict:
    return load_demo_report()


def chart_config() -> dict:
    return {
        "displaylogo": False,
        "responsive": True,
        "toImageButtonOptions": {"format": "png", "filename": "groupdna_chart", "scale": 2},
        "modeBarButtonsToAdd": ["drawline", "drawrect", "eraseshape"],
    }


def chart_theme() -> str:
    theme = st.session_state.get("theme_mode", "Dark")
    return CHART_TEMPLATE_DARK if theme == "Dark" else CHART_TEMPLATE_LIGHT


def get_report() -> dict | None:
    return st.session_state.get("report")


def ensure_demo_available() -> None:
    if "report" not in st.session_state and st.session_state.get("use_demo", True):
        st.session_state["report"] = cached_demo_report()
        st.session_state["source_name"] = "Bundled demo chat"


def sidebar() -> str:
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.caption(APP_SUBTITLE)
        page = st.radio("Navigation", SIDEBAR_PAGES, label_visibility="collapsed")
        st.divider()
        st.session_state["theme_mode"] = st.selectbox("Theme", ["Dark", "Light"], index=0)
        st.session_state["upload_limit_mb"] = st.selectbox(
            "Upload size limit",
            UPLOAD_SIZE_OPTIONS_MB,
            index=UPLOAD_SIZE_OPTIONS_MB.index(st.session_state.get("upload_limit_mb", DEFAULT_UPLOAD_SIZE_MB)),
        )
        st.session_state["animations"] = st.toggle("Animations", value=st.session_state.get("animations", True))
        st.session_state["use_demo"] = st.toggle("Load demo insights", value=st.session_state.get("use_demo", True))
        if has_report():
            summary = st.session_state["report"].get("group_overview", {}).get("summary", {})
            st.success(f"{summary.get('total_messages', 0):,} messages loaded")
        else:
            st.info("No chat loaded yet")
    return page


def apply_filters(report: dict) -> pd.DataFrame:
    frame = chat_dataframe(report)
    if frame.empty:
        return frame

    with st.expander("Filters and Search", expanded=False):
        col1, col2, col3 = st.columns(3)
        min_date, max_date = frame["date"].min(), frame["date"].max()
        with col1:
            date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            members = st.multiselect("Members", sorted(frame["sender"].unique()), default=[])
        with col2:
            keyword = st.text_input("Keyword or phrase")
            length = st.slider("Message length", 0, int(frame["length"].max()), (0, int(frame["length"].max())))
            years = st.multiselect("Year", sorted(frame["year"].unique()), default=[])
        with col3:
            media_only = st.checkbox("Media only")
            deleted_only = st.checkbox("Deleted only")
            questions_only = st.checkbox("Questions only")
            caps_only = st.checkbox("Caps only")
            night_only = st.checkbox("Night messages")
            weekend_only = st.checkbox("Weekend")

    filtered = frame.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        filtered = filtered[(filtered["date"] >= date_range[0]) & (filtered["date"] <= date_range[1])]
    if members:
        filtered = filtered[filtered["sender"].isin(members)]
    if years:
        filtered = filtered[filtered["year"].isin(years)]
    if keyword:
        filtered = filtered[filtered["text"].str.contains(keyword, case=False, na=False, regex=False)]
    filtered = filtered[(filtered["length"] >= length[0]) & (filtered["length"] <= length[1])]
    if media_only:
        filtered = filtered[filtered["is_media"]]
    if deleted_only:
        filtered = filtered[filtered["is_deleted"]]
    if questions_only:
        filtered = filtered[filtered["is_question"]]
    if caps_only:
        filtered = filtered[filtered["is_caps"]]
    if night_only:
        filtered = filtered[filtered["is_night"]]
    if weekend_only:
        filtered = filtered[filtered["is_weekend"]]
    return filtered


def page_home() -> None:
    hero(APP_NAME, APP_SUBTITLE)
    report = get_report()
    if report:
        summary = report.get("group_overview", {}).get("summary", {})
        cols = st.columns(4)
        with cols[0]:
            metric_card("Messages", summary.get("total_messages", 0), "Parsed and indexed")
        with cols[1]:
            metric_card("Participants", summary.get("total_participants", 0), "Detected members")
        with cols[2]:
            metric_card("Duration", f"{summary.get('duration_days', 0)} days", "Conversation span")
        with cols[3]:
            metric_card("Avg / Day", summary.get("average_messages_per_day", 0), "Group pulse")

    st.markdown("## What GroupDNA does")
    col1, col2, col3 = st.columns(3)
    col1.markdown("**Upload** a WhatsApp `.txt` export and keep it in memory only.")
    col2.markdown("**Explore** activity, words, responses, heatmaps, timelines, and member behavior.")
    col3.markdown("**Export** CSV, JSON, Excel, HTML, PDF, and PNG chart snapshots.")
    st.markdown("## Quick start")
    if st.button("Upload a WhatsApp Chat", type="primary", use_container_width=True):
        st.session_state["page_override"] = "Upload Chat"
        st.rerun()


def page_upload() -> None:
    page_title("Upload Chat", "Drop in an exported WhatsApp .txt file. GroupDNA validates it before analytics begin.")
    limit_mb = st.session_state.get("upload_limit_mb", DEFAULT_UPLOAD_SIZE_MB)
    upload = st.file_uploader("WhatsApp .txt export", type=["txt"], accept_multiple_files=False)
    if not upload:
        st.info(f"Accepted format: .txt. Current upload limit: {limit_mb} MB.")
        return

    if not upload.name.lower().endswith(".txt"):
        st.error("That file type is not supported. Please upload the raw WhatsApp .txt export.")
        return

    size_mb = upload.size / (1024 * 1024)
    if size_mb > limit_mb:
        st.warning(
            f"This chat is {size_mb:.1f} MB, which is larger than the configured {limit_mb} MB limit. "
            "Large exports can make the browser slow, so GroupDNA stopped before parsing. Change the limit in Settings if this is expected."
        )
        return

    progress = st.progress(0)
    stage = st.empty()
    try:
        stage.write("Reading encrypted-free WhatsApp text export...")
        progress.progress(20)
        raw = upload.getvalue().decode("utf-8", errors="replace")
        stage.write("Parsing messages, senders, timestamps, and multiline entries...")
        progress.progress(45)
        report = cached_analyze_chat(raw)
        stage.write("Building dashboards and derived metrics...")
        progress.progress(80)
        st.session_state["report"] = report
        st.session_state["source_name"] = upload.name
        progress.progress(100)
        stage.success("Analysis complete.")
    except Exception as exc:
        st.error(f"GroupDNA could not parse this export: {exc}")
        return

    validation_report(report)


def validation_report(report: dict) -> None:
    validation = report.get("validation", {})
    summary = report.get("group_overview", {}).get("summary", {})
    cols = st.columns(4)
    cols[0].metric("Messages parsed", f"{validation.get('valid_messages', summary.get('total_messages', 0)):,}")
    cols[1].metric("Participants", f"{summary.get('total_participants', 0):,}")
    cols[2].metric("Date range", f"{summary.get('duration_days', 0):,} days")
    cols[3].metric("Errors", len(validation.get("errors", [])))
    st.dataframe(pd.DataFrame([validation]).T.rename(columns={0: "count"}), use_container_width=True)
    if validation.get("errors"):
        st.error("\n".join(validation["errors"][:5]))


def page_dashboard() -> None:
    report = require_report()
    if not report:
        return
    summary = report.get("group_overview", {}).get("summary", {})
    page_title("Dashboard", "A high-level replay of the group’s personality, pace, and peaks.")
    filtered = apply_filters(report)
    cols = st.columns(4)
    metrics = [
        ("Total Messages", len(filtered) if not filtered.empty else summary.get("total_messages", 0)),
        ("Participants", filtered["sender"].nunique() if not filtered.empty else summary.get("total_participants", 0)),
        ("Duration", f"{summary.get('duration_days', 0):,} days"),
        ("Avg Messages / Day", summary.get("average_messages_per_day", 0)),
        ("Media Messages", summary.get("media_messages", 0)),
        ("Deleted Messages", summary.get("deleted_messages", 0)),
        ("System Messages", summary.get("system_messages", 0)),
        ("Avg Length", summary.get("average_message_length", 0)),
        ("Longest Message", summary.get("longest_message", 0)),
        ("Shortest Message", summary.get("shortest_message", 0)),
        ("Most Active Day", summary.get("most_active_day", ("", 0))[0]),
        ("Most Active Hour", f"{summary.get('most_active_hour', (0, 0))[0]}:00"),
    ]
    for index, (label, value) in enumerate(metrics):
        with cols[index % 4]:
            metric_card(label, value)

    leaderboard = leaderboard_dataframe(report)
    activity = report.get("activity_summary", {})
    c1, c2 = st.columns((1.2, 1))
    with c1:
        st.plotly_chart(charts.line_activity(activity.get("daily_activity", {}), chart_theme()), use_container_width=True, config=chart_config())
    with c2:
        st.plotly_chart(charts.leaderboard_bar(leaderboard, chart_theme(), 15), use_container_width=True, config=chart_config())
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(charts.hourly_bar(activity.get("hourly_activity", {}), chart_theme()), use_container_width=True, config=chart_config())
    with c4:
        st.plotly_chart(charts.donut(activity.get("weekend_vs_weekday", {}).keys(), activity.get("weekend_vs_weekday", {}).values(), "Weekend vs Weekday", chart_theme()), use_container_width=True, config=chart_config())


def page_activity() -> None:
    report = require_report()
    if not report:
        return
    page_title("Activity Analysis", "Daily, weekly, monthly, yearly, hourly, weekend, and spike patterns.")
    activity = report.get("activity_summary", {})
    tabs = st.tabs(["Daily", "Hourly", "Monthly", "Yearly", "Spikes"])
    with tabs[0]:
        st.plotly_chart(charts.line_activity(activity.get("daily_activity", {}), chart_theme()), use_container_width=True, config=chart_config())
    with tabs[1]:
        st.plotly_chart(charts.hourly_bar(activity.get("hourly_activity", {}), chart_theme()), use_container_width=True, config=chart_config())
    with tabs[2]:
        st.plotly_chart(charts.monthly_line(activity.get("monthly_activity", {}), chart_theme()), use_container_width=True, config=chart_config())
        st.plotly_chart(charts.weekly_area(activity.get("weekly_activity", {}), chart_theme()), use_container_width=True, config=chart_config())
    with tabs[3]:
        yearly = pd.DataFrame(activity.get("yearly_activity", {}).items(), columns=["year", "messages"])
        st.bar_chart(yearly, x="year", y="messages", use_container_width=True)
    with tabs[4]:
        frame = pd.DataFrame(activity.get("daily_activity", {}).items(), columns=["date", "messages"]).sort_values("messages", ascending=False)
        st.dataframe(frame.head(25), use_container_width=True)


def page_words() -> None:
    report = require_report()
    if not report:
        return
    page_title("Word Analytics", "Vocabulary, phrases, per-member language habits, and message length patterns.")
    words = report.get("word_statistics", {})
    cols = st.columns(4)
    cols[0].metric("Valid words", f"{words.get('total_valid_words', 0):,}")
    cols[1].metric("Unique words", f"{words.get('unique_words', 0):,}")
    cols[2].metric("Vocabulary richness", words.get("vocabulary_richness", 0))
    cols[3].metric("Language types", len(words.get("language_distribution", {})))
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.top_words_bar(top_words_dataframe(report, 35), chart_theme()), use_container_width=True, config=chart_config())
    with c2:
        st.plotly_chart(charts.message_length_distribution(words.get("message_length_distribution", []), chart_theme()), use_container_width=True, config=chart_config())
    c3, c4 = st.columns(2)
    chat_frame = chat_dataframe(report)
    with c3:
        st.plotly_chart(charts.box_by_member(chat_frame, chart_theme()), use_container_width=True, config=chart_config())
    with c4:
        st.plotly_chart(charts.violin_by_member(chat_frame, chart_theme()), use_container_width=True, config=chart_config())
    render_wordcloud(words.get("word_frequency", {}))
    st.subheader("Top words per member")
    member = st.selectbox("Member", sorted(report.get("members", {}).keys()))
    st.dataframe(pd.DataFrame(words.get("top_words_per_member", {}).get(member, []), columns=["word", "count"]), use_container_width=True)
    st.subheader("Common phrases")
    st.dataframe(pd.DataFrame(words.get("common_phrases", []), columns=["phrase", "count"]), use_container_width=True)


def page_response() -> None:
    report = require_report()
    if not report:
        return
    page_title("Response Analysis", "Who replies fast, who starts conversations, and where the silences happen.")
    response = report.get("response_analysis", {})
    fast = response.get("fastest_responder")
    slow = response.get("slowest_responder")
    cols = st.columns(4)
    cols[0].metric("Fastest responder", fast[0] if fast else "N/A")
    cols[1].metric("Fastest avg min", f"{fast[1]:.1f}" if fast else "N/A")
    cols[2].metric("Slowest responder", slow[0] if slow else "N/A")
    cols[3].metric("Reply bursts", len(response.get("conversation_bursts", [])))
    st.plotly_chart(charts.response_scatter(response_dataframe(report), chart_theme()), use_container_width=True, config=chart_config())
    st.plotly_chart(
        charts.response_bubble(response_dataframe(report), leaderboard_dataframe(report), chart_theme()),
        use_container_width=True,
        config=chart_config(),
    )
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Conversation starters")
        st.dataframe(pd.DataFrame(response.get("conversation_starters", []), columns=["member", "starts"]), use_container_width=True)
    with c2:
        st.subheader("Silent streaks")
        streaks = [{"member": m, **d} for m, d in response.get("silent_streaks", {}).items()]
        st.dataframe(pd.DataFrame(streaks).sort_values("days", ascending=False), use_container_width=True)


def page_personality() -> None:
    report = require_report()
    if not report:
        return
    page_title("Personality Lab", "Archetype detection with scores, confidence, evidence, and runner-ups.")
    frame = archetype_dataframe(report)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.archetype_treemap(frame, chart_theme()), use_container_width=True, config=chart_config())
    with c2:
        st.plotly_chart(charts.archetype_sunburst(frame, chart_theme()), use_container_width=True, config=chart_config())
    archetypes = sorted(frame["archetype"].dropna().unique()) if not frame.empty else []
    selected = st.selectbox("Archetype", archetypes)
    st.dataframe(frame[frame["archetype"] == selected].sort_values("score", ascending=False), use_container_width=True)
    member = st.selectbox("Inspect member", sorted(report.get("members", {}).keys()), key="personality_member")
    details = report["members"][member]
    st.plotly_chart(charts.radar(details.get("personality_scores", {}), member, chart_theme()), use_container_width=True, config=chart_config())
    st.markdown(f"**Assigned:** {details.get('archetype')}  \n**Runner-up:** {details.get('runner_up_archetype')}")
    st.write(archetype_explanation(details))


def page_member() -> None:
    report = require_report()
    if not report:
        return
    page_title("Member Explorer", "Click into any participant’s personal dashboard.")
    members = report.get("members", {})
    member = st.selectbox("Participant", sorted(members.keys()))
    data = members[member]
    cols = st.columns(4)
    for index, key in enumerate(["messages", "words", "media", "deleted", "average_length", "burst_score", "ghost_score", "question_ratio"]):
        cols[index % 4].metric(key.replace("_", " ").title(), data.get(key, 0))
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.radar(data.get("personality_scores", {}), f"{member} personality", chart_theme()), use_container_width=True, config=chart_config())
    with c2:
        st.dataframe(pd.DataFrame(data.get("favorite_words", []), columns=["word", "count"]), use_container_width=True)
    st.subheader("Conversation timeline")
    timeline = pd.DataFrame(data.get("timeline", []))
    st.dataframe(timeline[["timestamp", "sender", "text"]] if not timeline.empty else timeline, use_container_width=True, height=420)


def page_timeline() -> None:
    report = require_report()
    if not report:
        return
    page_title("Timeline", "Search, zoom, and jump through the chat chronologically.")
    frame = apply_filters(report).sort_values("timestamp", ascending=False)
    st.plotly_chart(charts.animated_monthly_members(chat_dataframe(report), chart_theme()), use_container_width=True, config=chart_config())
    st.dataframe(frame[["timestamp", "sender", "text", "length"]].head(1000), use_container_width=True, height=620)


def page_heatmaps() -> None:
    report = require_report()
    if not report:
        return
    page_title("Heatmaps", "Daily, weekly, monthly, hourly, member, and calendar heatmaps.")
    activity = report.get("activity_summary", {})
    members = list(report.get("members", {}).keys())[:35]
    st.plotly_chart(charts.heatmap(activity.get("activity_heatmap", {}), chart_theme()), use_container_width=True, config=chart_config())
    st.plotly_chart(charts.member_hour_heatmap(activity.get("member_hour_heatmap", {}), members, chart_theme()), use_container_width=True, config=chart_config())
    st.plotly_chart(charts.member_day_heatmap(activity.get("member_day_heatmap", {}), members, chart_theme()), use_container_width=True, config=chart_config())
    st.plotly_chart(charts.calendar_heatmap(activity.get("daily_activity", {}), chart_theme()), use_container_width=True, config=chart_config())


def page_comparisons() -> None:
    report = require_report()
    if not report:
        return
    page_title("Comparisons", "Select 2 to 5 members and compare everything side by side.")
    members = sorted(report.get("members", {}).keys())
    selected = st.multiselect("Members", members, default=members[: min(3, len(members))], max_selections=5)
    if len(selected) < 2:
        st.warning("Choose at least two members.")
        return
    st.plotly_chart(charts.comparison_radar(report.get("members", {}), selected, chart_theme()), use_container_width=True, config=chart_config())
    rows = []
    for member in selected:
        row = {"member": member}
        row.update({k: v for k, v in report["members"][member].items() if isinstance(v, (int, float, str))})
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def page_export() -> None:
    report = require_report()
    if not report:
        return
    page_title("Export Report", "Download the report in portable formats. Uploaded chats are not stored permanently.")
    col1, col2, col3 = st.columns(3)
    col1.download_button("CSV messages", chat_to_csv(report), "groupdna_messages.csv", "text/csv", use_container_width=True)
    col2.download_button("JSON report", report_to_json(report), "groupdna_report.json", "application/json", use_container_width=True)
    col3.download_button("Excel workbook", chat_to_excel(report), "groupdna_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    col4, col5 = st.columns(2)
    col4.download_button("HTML report", report_to_html(report), "groupdna_report.html", "text/html", use_container_width=True)
    col5.download_button("PDF report", report_to_pdf_bytes(report), "groupdna_report.pdf", "application/pdf", use_container_width=True)
    st.plotly_chart(charts.sankey_top_transitions(report.get("chat_data", []), chart_theme()), use_container_width=True, config=chart_config())


def page_feedback() -> None:
    page_title("Feedback", "Suggest features, report bugs, or rate the experience.")
    with st.form("feedback"):
        name = st.text_input("Name")
        email = st.text_input("Email (optional)")
        kind = st.selectbox("Type", ["Suggestion", "Bug", "Feature Request"])
        rating = st.slider("Rating", 1, 5, 5)
        message = st.text_area("Comment")
        screenshot = st.file_uploader("Screenshot (optional)", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Submit feedback", type="primary")
    if submitted:
        save_feedback(name, email, kind, rating, message, screenshot.name if screenshot else None)
        st.balloons()
        st.success("Thank you. Your feedback was saved locally in SQLite.")


def page_settings() -> None:
    page_title("Settings", "Tune theme, chart colors, upload limits, animation, and export preferences.")
    st.selectbox("Theme", ["Dark", "Light"], key="theme_mode")
    st.selectbox("Upload size", UPLOAD_SIZE_OPTIONS_MB, key="upload_limit_mb")
    st.toggle("Animation toggle", key="animations")
    st.checkbox("Include raw messages in exports", value=True)
    st.checkbox("Prefer PDF exports", value=True)
    st.info("Privacy: uploaded chats are held in Streamlit session memory only unless you download an export.")


def page_about() -> None:
    page_title("About", "Architecture, backend, frontend, libraries, version, and project links.")
    st.markdown(
        f"""
        **{APP_NAME}** turns WhatsApp text exports into an interactive analytics replay.

        **Backend:** notebook-derived parser, group overview, activity summary, word statistics, response analysis,
        personality archetypes, validation, and report generation.

        **Frontend:** Streamlit, Plotly, pandas, custom CSS, cached analysis pipeline, SQLite feedback.

        **Version:** {VERSION}

        **Security:** uploads stay in memory and are not written to disk by the app.
        """
    )


def require_report() -> dict | None:
    ensure_demo_available()
    report = get_report()
    if not report or not report.get("chat_data"):
        empty_state()
        return None
    return report


def archetype_explanation(details: dict) -> str:
    assigned = details.get("archetype")
    runner = details.get("runner_up_archetype")
    return (
        f"{assigned} was assigned because this member's strongest normalized behavior score wins across the archetype model. "
        f"Supporting metrics include burst score {details.get('burst_score')}, question ratio {details.get('question_ratio')}, "
        f"night activity {details.get('night_activity')}, ghost score {details.get('ghost_score')}, and average length {details.get('average_length')}. "
        f"The runner-up was {runner}, which means the profile has a visible secondary style but less evidence than the winning archetype."
    )


def render_wordcloud(frequency: dict) -> None:
    st.subheader("Word cloud")
    try:
        from wordcloud import WordCloud

        image = WordCloud(width=1400, height=520, background_color=None, mode="RGBA", colormap="viridis").generate_from_frequencies(frequency)
        buffer = BytesIO()
        image.to_image().save(buffer, format="PNG")
        st.image(buffer.getvalue(), use_container_width=True)
        st.download_button("Download word cloud PNG", buffer.getvalue(), "groupdna_wordcloud.png", "image/png", use_container_width=True)
    except Exception:
        st.info("Install `wordcloud` to render the generated word cloud. The ranked word table remains available below.")


def save_feedback(name: str, email: str, kind: str, rating: int, message: str, screenshot: str | None) -> None:
    FEEDBACK_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(FEEDBACK_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                email TEXT,
                kind TEXT,
                rating INTEGER,
                message TEXT,
                screenshot TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO feedback(name, email, kind, rating, message, screenshot) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, kind, rating, message, screenshot),
        )


PAGES = {
    "Home": page_home,
    "Upload Chat": page_upload,
    "Dashboard": page_dashboard,
    "Activity Analysis": page_activity,
    "Word Analytics": page_words,
    "Response Analysis": page_response,
    "Personality Lab": page_personality,
    "Member Explorer": page_member,
    "Timeline": page_timeline,
    "Heatmaps": page_heatmaps,
    "Comparisons": page_comparisons,
    "Export Report": page_export,
    "Feedback": page_feedback,
    "Settings": page_settings,
    "About": page_about,
}


def main() -> None:
    ensure_demo_available()
    page = st.session_state.pop("page_override", None) or sidebar()
    PAGES.get(page, page_home)()


if __name__ == "__main__":
    main()
