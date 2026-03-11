from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
from app import app

try:
    from data.db import get_team_names, get_conference_names
    TEAM_NAMES = get_team_names()
    CONFERENCE_NAMES = get_conference_names()
except Exception:
    TEAM_NAMES, CONFERENCE_NAMES = [], []

# ─────────────────────────────────────────────────────────────────────────────
# Nav items
# ─────────────────────────────────────────────────────────────────────────────
NAV_LINKS = [
    ("HOME",       "/"),
    ("TEAMS",      "/team-rankings"),
    ("PLAYERS",    "/player-rankings"),
    ("RESUME",     "/teams-resume"),
    ("BRACKETS",   "/conf-brackets"),
    ("CHALLENGES", "/coaches-challenges"),
    ("JOBS",       "/hc-jobs"),
    ("PORTAL",     "/portal"),
]

NAVBAR = html.Div(
    html.Div(
        [
            dbc.NavLink(label, href=href, style={
                "color": "white", "fontWeight": "bold",
                "fontSize": "0.9rem", "padding": "0 0.75rem",
            })
            for label, href in NAV_LINKS
        ],
        style={"display": "flex", "alignItems": "center", "justifyContent": "center", "height": "100%"},
    ),
    style={
        "backgroundColor": "#505050",
        "height": "52px",
        "position": "fixed", "top": 0, "left": 0, "right": 0,
        "zIndex": 1000,
        "display": "flex", "alignItems": "center",
        "justifyContent": "center",
        "width": "100%",
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar (global filters)
# ─────────────────────────────────────────────────────────────────────────────
SIDEBAR_STYLE = {
    "width": "260px", "minWidth": "260px", "backgroundColor": "#F2F2F2",
    "padding": "1rem", "borderRight": "1px solid #dee2e6",
    "height": "calc(100vh - 52px)", "overflowY": "auto",
    "position": "fixed", "top": "52px", "left": 0,
}

SIDEBAR = html.Div([
    html.H4("Basketball Analytics", className="mb-3 mt-2"),
    html.Hr(),
    html.H6("FILTERS", className="text-uppercase text-muted mb-3"),

    html.Label("Split", className="fw-semibold"),
    dcc.Dropdown(
        id="split",
        options=["Full Season", "Conference", "Non-Conference", "Home", "Away", "Neutral"],
        value="Full Season", clearable=False, className="mb-3",
    ),

    html.Label("Conference Tier", className="fw-semibold"),
    dcc.Dropdown(
        id="tier",
        options=["All", "High Major", "Mid Major", "One Bid", "Low Major"],
        value="All", clearable=False, className="mb-3",
    ),

    html.Label("Conferences", className="fw-semibold"),
    dcc.Dropdown(
        id="conferences",
        options=[{"label": c, "value": c} for c in CONFERENCE_NAMES],
        multi=True, placeholder="Choose conferences...", className="mb-3",
    ),

    html.Label("Teams", className="fw-semibold"),
    dcc.Dropdown(
        id="teams",
        options=[{"label": t, "value": t} for t in TEAM_NAMES],
        multi=True, placeholder="Choose teams...", className="mb-3",
    ),
], id="sidebar", style=SIDEBAR_STYLE)

# ─────────────────────────────────────────────────────────────────────────────
# Root layout
# ─────────────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="sort-col", data=None),
    NAVBAR,
    SIDEBAR,
    html.Div(
        id="page-content",
        style={"marginLeft": "260px", "marginTop": "52px", "padding": "1.5rem"},
    ),
])