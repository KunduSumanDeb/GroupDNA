"""Configuration for GroupDNA."""

from __future__ import annotations

APP_NAME = "GroupDNA"
APP_SUBTITLE = "Decode Your WhatsApp Group."
VERSION = "1.0.0"

UPLOAD_SIZE_OPTIONS_MB = [10, 25, 50, 100]
DEFAULT_UPLOAD_SIZE_MB = 25

PRIMARY_COLOR = "#7c3aed"
ACCENT_COLOR = "#06b6d4"
SUCCESS_COLOR = "#22c55e"
WARNING_COLOR = "#f59e0b"
ERROR_COLOR = "#ef4444"

CHART_TEMPLATE_DARK = "plotly_dark"
CHART_TEMPLATE_LIGHT = "plotly_white"

SIDEBAR_PAGES = [
    "Home",
    "Upload Chat",
    "Dashboard",
    "Activity Analysis",
    "Word Analytics",
    "Response Analysis",
    "Personality Lab",
    "Member Explorer",
    "Timeline",
    "Heatmaps",
    "Comparisons",
    "Export Report",
    "Feedback",
    "Settings",
    "About",
]
