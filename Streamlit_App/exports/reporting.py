"""CSV, JSON, HTML, and lightweight PDF export helpers."""

from __future__ import annotations

import io
import json
from datetime import datetime

import pandas as pd


def report_to_json(report: dict) -> str:
    def default(value):
        if isinstance(value, (datetime,)):
            return value.isoformat()
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    return json.dumps(report, default=default, indent=2)


def chat_to_csv(report: dict) -> str:
    frame = pd.DataFrame(report.get("chat_data", []))
    return frame.to_csv(index=False)


def chat_to_excel(report: dict) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(report.get("chat_data", [])).to_excel(writer, sheet_name="Messages", index=False)
        pd.DataFrame(report.get("group_overview", {}).get("leaderboard", []), columns=["Member", "Messages"]).to_excel(
            writer, sheet_name="Leaderboard", index=False
        )
        pd.DataFrame(report.get("word_statistics", {}).get("top_words", []), columns=["Word", "Count"]).to_excel(
            writer, sheet_name="Top Words", index=False
        )
    return output.getvalue()


def report_to_html(report: dict) -> str:
    summary = report.get("group_overview", {}).get("summary", {})
    top_words = report.get("word_statistics", {}).get("top_words", [])[:15]
    leaderboard = report.get("group_overview", {}).get("leaderboard", [])[:15]
    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>GroupDNA Report</title>
      <style>
        body {{ font-family: Inter, Arial, sans-serif; background:#0f172a; color:#e5e7eb; padding:40px; }}
        section {{ background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12); border-radius:18px; padding:24px; margin:20px 0; }}
        h1 {{ font-size:44px; margin-bottom:0; }}
        .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; }}
        .metric {{ background:rgba(124,58,237,.22); padding:18px; border-radius:14px; }}
        .value {{ font-size:28px; font-weight:800; }}
      </style>
    </head>
    <body>
      <h1>GroupDNA</h1>
      <p>Decode Your WhatsApp Group.</p>
      <section class="grid">
        {metric('Messages', summary.get('total_messages', 0))}
        {metric('Participants', summary.get('total_participants', 0))}
        {metric('Duration', str(summary.get('duration_days', 0)) + ' days')}
        {metric('Avg / Day', summary.get('average_messages_per_day', 0))}
      </section>
      <section>
        <h2>Leaderboard</h2>
        <ol>{''.join(f'<li>{name}: {count:,}</li>' for name, count in leaderboard)}</ol>
      </section>
      <section>
        <h2>Top Words</h2>
        <ol>{''.join(f'<li>{word}: {count:,}</li>' for word, count in top_words)}</ol>
      </section>
    </body>
    </html>
    """


def metric(label, value) -> str:
    return f'<div class="metric"><div>{label}</div><div class="value">{value}</div></div>'


def report_to_pdf_bytes(report: dict) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception:
        return report_to_html(report).encode("utf-8")

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=letter)
    width, height = letter
    summary = report.get("group_overview", {}).get("summary", {})
    pdf.setTitle("GroupDNA Report")
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(50, height - 60, "GroupDNA Report")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 85, "Decode Your WhatsApp Group.")
    y = height - 130
    for label, value in [
        ("Total Messages", summary.get("total_messages", 0)),
        ("Participants", summary.get("total_participants", 0)),
        ("Duration", f"{summary.get('duration_days', 0)} days"),
        ("Average Messages / Day", summary.get("average_messages_per_day", 0)),
        ("Media Messages", summary.get("media_messages", 0)),
        ("Deleted Messages", summary.get("deleted_messages", 0)),
    ]:
        pdf.drawString(50, y, f"{label}: {value}")
        y -= 22
    pdf.showPage()
    pdf.save()
    return output.getvalue()
