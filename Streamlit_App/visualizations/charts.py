"""Reusable Plotly visualizations."""

from __future__ import annotations

import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from backend.analytics import weekday_names


PALETTE = ["#7c3aed", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6", "#eab308"]


def configure(fig: go.Figure, title: str | None = None, template: str = "plotly_dark") -> go.Figure:
    fig.update_layout(
        template=template,
        title=title,
        colorway=PALETTE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=24, r=24, t=56 if title else 24, b=24),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,.2)")
    return fig


def line_activity(daily_activity: dict, template: str) -> go.Figure:
    frame = pd.DataFrame({"date": list(daily_activity.keys()), "messages": list(daily_activity.values())})
    fig = px.area(frame, x="date", y="messages", markers=True)
    return configure(fig, "Daily Activity", template)


def hourly_bar(hourly_activity: dict, template: str) -> go.Figure:
    frame = pd.DataFrame({"hour": list(range(24)), "messages": [hourly_activity.get(hour, 0) for hour in range(24)]})
    fig = px.bar(frame, x="hour", y="messages", text_auto=True)
    return configure(fig, "Messages by Hour", template)


def leaderboard_bar(frame: pd.DataFrame, template: str, limit: int = 20) -> go.Figure:
    data = frame.head(limit).sort_values("messages")
    fig = px.bar(data, x="messages", y="member", orientation="h", color="messages", color_continuous_scale="Viridis")
    return configure(fig, "Most Active Members", template)


def donut(labels, values, title: str, template: str) -> go.Figure:
    fig = go.Figure(data=[go.Pie(labels=list(labels), values=list(values), hole=0.62)])
    return configure(fig, title, template)


def heatmap(activity_heatmap: dict, template: str, title: str = "Weekday x Hour Heatmap") -> go.Figure:
    days = weekday_names()
    z = [[activity_heatmap.get(day, {}).get(hour, 0) for hour in range(24)] for day in days]
    fig = go.Figure(data=go.Heatmap(z=z, x=list(range(24)), y=days, colorscale="Viridis", hoverongaps=False))
    fig.update_xaxes(title="Hour")
    fig.update_yaxes(title="Day")
    return configure(fig, title, template)


def member_hour_heatmap(member_hour: dict, members: list[str], template: str) -> go.Figure:
    z = [[member_hour.get(member, {}).get(hour, 0) for hour in range(24)] for member in members]
    fig = go.Figure(data=go.Heatmap(z=z, x=list(range(24)), y=members, colorscale="Turbo"))
    return configure(fig, "Member x Hour", template)


def member_day_heatmap(member_day: dict, members: list[str], template: str) -> go.Figure:
    days = weekday_names()
    z = [[member_day.get(member, {}).get(day, 0) for day in days] for member in members]
    fig = go.Figure(data=go.Heatmap(z=z, x=days, y=members, colorscale="Magma"))
    return configure(fig, "Member x Day", template)


def top_words_bar(frame: pd.DataFrame, template: str) -> go.Figure:
    data = frame.sort_values("count")
    fig = px.bar(data, x="count", y="word", orientation="h", color="count", color_continuous_scale="Plasma")
    return configure(fig, "Top Words", template)


def message_length_distribution(lengths: list[int], template: str) -> go.Figure:
    fig = px.histogram(pd.DataFrame({"length": lengths}), x="length", nbins=60, marginal="box")
    return configure(fig, "Message Length Distribution", template)


def response_scatter(frame: pd.DataFrame, template: str) -> go.Figure:
    data = frame.sort_values("avg_response_minutes").head(50)
    fig = px.scatter(data, x="member", y="avg_response_minutes", size="avg_response_minutes", color="avg_response_minutes")
    fig.update_xaxes(tickangle=45)
    return configure(fig, "Average Response Time", template)


def response_bubble(frame: pd.DataFrame, leaderboard: pd.DataFrame, template: str) -> go.Figure:
    if frame.empty or leaderboard.empty:
        return configure(go.Figure(), "Response Time vs Volume", template)
    data = frame.merge(leaderboard, on="member", how="left").fillna(0).head(60)
    fig = px.scatter(
        data,
        x="messages",
        y="avg_response_minutes",
        size="messages",
        color="avg_response_minutes",
        hover_name="member",
        color_continuous_scale="Turbo",
    )
    return configure(fig, "Response Time vs Volume", template)


def radar(scores: dict, title: str, template: str) -> go.Figure:
    categories = list(scores.keys())
    values = [scores[key] for key in categories]
    if categories:
        categories = categories + [categories[0]]
        values = values + [values[0]]
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill="toself", name=title))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
    return configure(fig, title, template)


def archetype_treemap(frame: pd.DataFrame, template: str) -> go.Figure:
    if frame.empty:
        return configure(go.Figure(), "Archetype Map", template)
    fig = px.treemap(frame, path=["archetype", "member"], values="score", color="score", color_continuous_scale="Viridis")
    return configure(fig, "Personality Archetype Map", template)


def archetype_sunburst(frame: pd.DataFrame, template: str) -> go.Figure:
    if frame.empty:
        return configure(go.Figure(), "Archetype Sunburst", template)
    fig = px.sunburst(frame, path=["archetype", "member"], values="score", color="archetype")
    return configure(fig, "Archetype Sunburst", template)


def monthly_line(monthly_activity: dict, template: str) -> go.Figure:
    frame = pd.DataFrame({"month": list(monthly_activity.keys()), "messages": list(monthly_activity.values())})
    fig = px.line(frame, x="month", y="messages", markers=True)
    return configure(fig, "Monthly Trend", template)


def weekly_area(weekly_activity: dict, template: str) -> go.Figure:
    frame = pd.DataFrame({"week": list(weekly_activity.keys()), "messages": list(weekly_activity.values())})
    fig = px.area(frame, x="week", y="messages")
    fig.update_xaxes(tickangle=45)
    return configure(fig, "Weekly Activity", template)


def box_by_member(chat_frame: pd.DataFrame, template: str) -> go.Figure:
    if chat_frame.empty:
        return configure(go.Figure(), "Message Length Box Plot", template)
    top_members = chat_frame["sender"].value_counts().head(20).index
    data = chat_frame[chat_frame["sender"].isin(top_members)]
    fig = px.box(data, x="sender", y="length", color="sender")
    fig.update_xaxes(tickangle=45)
    return configure(fig, "Message Length Box Plot", template)


def violin_by_member(chat_frame: pd.DataFrame, template: str) -> go.Figure:
    if chat_frame.empty:
        return configure(go.Figure(), "Message Length Violin Plot", template)
    top_members = chat_frame["sender"].value_counts().head(12).index
    data = chat_frame[chat_frame["sender"].isin(top_members)]
    fig = px.violin(data, x="sender", y="length", color="sender", box=True)
    fig.update_xaxes(tickangle=45)
    return configure(fig, "Message Length Violin Plot", template)


def animated_monthly_members(chat_frame: pd.DataFrame, template: str) -> go.Figure:
    if chat_frame.empty:
        return configure(go.Figure(), "Animated Monthly Leaders", template)
    top_members = chat_frame["sender"].value_counts().head(12).index
    data = (
        chat_frame[chat_frame["sender"].isin(top_members)]
        .groupby(["month", "sender"])
        .size()
        .reset_index(name="messages")
        .sort_values("month")
    )
    fig = px.bar(data, x="sender", y="messages", color="sender", animation_frame="month", range_y=[0, max(data["messages"].max(), 1)])
    fig.update_xaxes(tickangle=45)
    return configure(fig, "Animated Monthly Leaders", template)


def comparison_radar(member_stats: dict, members: list[str], template: str) -> go.Figure:
    metrics = ["messages", "words", "media", "deleted", "question_ratio", "caps_ratio", "night_activity", "weekend_activity"]
    max_values = {metric: max([float(member_stats.get(member, {}).get(metric, 0) or 0) for member in members] + [1]) for metric in metrics}
    fig = go.Figure()
    for member in members:
        values = [float(member_stats.get(member, {}).get(metric, 0) or 0) / max_values[metric] for metric in metrics]
        fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=metrics + [metrics[0]], fill="toself", name=member))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
    return configure(fig, "Member Comparison", template)


def calendar_heatmap(daily_activity: dict, template: str) -> go.Figure:
    rows = []
    for day, count in daily_activity.items():
        ts = pd.Timestamp(day)
        rows.append(
            {
                "date": ts,
                "count": count,
                "weekday": calendar.day_name[ts.weekday()],
                "week": int(ts.strftime("%U")),
                "year": ts.year,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return configure(go.Figure(), "Calendar Heatmap", template)
    fig = px.density_heatmap(frame, x="week", y="weekday", z="count", facet_row="year", histfunc="sum", color_continuous_scale="Viridis")
    return configure(fig, "Calendar Heatmap", template)


def sankey_top_transitions(chat_data: list[dict], template: str) -> go.Figure:
    transitions = {}
    ordered = sorted(chat_data, key=lambda item: item["timestamp"])
    for previous, current in zip(ordered, ordered[1:]):
        if previous["sender"] != current["sender"]:
            key = (previous["sender"], current["sender"])
            transitions[key] = transitions.get(key, 0) + 1
    top = sorted(transitions.items(), key=lambda item: item[1], reverse=True)[:30]
    labels = sorted({name for pair, _ in top for name in pair})
    index = {label: i for i, label in enumerate(labels)}
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(label=labels, pad=15, thickness=14),
                link=dict(source=[index[a] for (a, _), _v in top], target=[index[b] for (_, b), _v in top], value=[v for _pair, v in top]),
            )
        ]
    )
    return configure(fig, "Conversation Flow", template)
