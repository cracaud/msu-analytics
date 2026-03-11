from dash import html, dcc, Input, Output, State, ALL, callback_context, no_update
import json
import pandas as pd
import os
from app import app

# ─────────────────────────────────────────────────────────────────────────────
# Formatters
# ─────────────────────────────────────────────────────────────────────────────
def fmt_mp(val):
    try:    return str(round(float(val)))
    except: return val

def fmt_per_min(val):
    try:    return f"{float(val):.1f}"
    except: return val

def fmt_2dec(val):
    try:    return f"{float(val):.2f}"
    except: return val

def fmt_pct(val):
    try:    return f"{float(val)*100:.1f}%"
    except: return val

def fmt_ile(val):
    v = str(val).strip().replace("%", "")
    try:
        f = float(v)
        return f"{f:.0f}%" if f > 1 else f"{f*100:.0f}%"
    except:
        return val

# ─────────────────────────────────────────────────────────────────────────────
# Data loader
# ─────────────────────────────────────────────────────────────────────────────
CLASS_ABBREV = {"Freshman": "FR", "Sophomore": "SO", "Junior": "JR", "Senior": "SR"}

def load_portal():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "portal_db.csv")
    df = pd.read_csv(path).fillna("-")
    df = df[df["status"].notna() & (df["status"].astype(str).str.strip() != "-") & (df["status"].astype(str).str.strip() != "nan")]
    players = []
    for _, row in df.iterrows():
        status = str(row["status"]).strip().upper()
        if status in ("NAN", "", "-"):
            status = "POTENTIAL"
        players.append({
            "status":                 status,
            "player":                 str(row["fullName"]).strip(),
            "class":                  CLASS_ABBREV.get(str(row["CLASS YR"]).strip(), str(row["CLASS YR"]).strip()),
            "size":                   str(row["HEIGHT"]).strip(),
            "position":               str(row["Pos"]).strip(),
            "current_team":           str(row["teamMarket"]).strip(),
            "gs":                     str(row["GS"]).strip(),
            "gp":                     str(row["GP"]).strip(),
            "mp":                     fmt_mp(str(row["MP"]).strip()),
            "extra_poss":             str(row["extra_poss"]).strip(),
            "extra_poss_pct":         fmt_ile(str(row["extra_poss_perc"]).strip()),
            "extra_poss_per_min":     fmt_per_min(str(row["extra_poss_per_40"]).strip()),
            "extra_poss_per_min_pct": fmt_ile(str(row["extra_poss_per_40_perc"]).strip()),
            "three_par":              fmt_pct(str(row["3PAr"]).strip()),
            "three_par_pct":          fmt_ile(str(row["3PAr %ile"]).strip()),
            "three_p":                fmt_pct(str(row["3P%"]).strip()),
            "three_p_pct":            fmt_ile(str(row["3P% %ile"]).strip()),
            "obpr":                   fmt_2dec(str(row["OBPR"]).strip()),
            "obpr_pct":               fmt_ile(str(row["OBPR_perct"]).strip()),
            "dbpr":                   fmt_2dec(str(row["DBPR"]).strip()),
            "dbpr_pct":               fmt_ile(str(row["DBPR_perct"]).strip()),
            "bpr":                    fmt_2dec(str(row["BPR"]).strip()),
            "bpr_pct":                fmt_ile(str(row["BPR_perct"]).strip()),
            "em_position":            fmt_per_min(str(row["Position"]).strip()),
            "em_role":                fmt_per_min(str(row["Role"]).strip()),
        })
    return players

PORTAL_PLAYERS = load_portal()

# Unique values for dropdowns
def unique_vals(key):
    return sorted({p[key] for p in PORTAL_PLAYERS if p[key] not in ("", "-")})

# ─────────────────────────────────────────────────────────────────────────────
# Status badge
# ─────────────────────────────────────────────────────────────────────────────
STATUS_STYLES = {
    "ENTERED":   ("#fef2f2", "#dc2626", "#fca5a5"),
    "COMMITTED": ("#eff6ff", "#1d4ed8", "#bfdbfe"),
    "POTENTIAL": ("#fefce8", "#a16207", "#fde68a"),
    "WITHDRAWN": ("#f8fafc", "#475569", "#cbd5e1"),
}

def status_badge(status):
    bg, color, border = STATUS_STYLES.get(status.upper(), ("#f8fafc", "#475569", "#cbd5e1"))
    return html.Span(status.upper(), style={
        "backgroundColor": bg, "color": color,
        "border": f"1px solid {border}", "borderRadius": "4px",
        "padding": "2px 8px", "fontSize": "0.65rem", "fontWeight": "700", "whiteSpace": "nowrap",
    })

# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────
TH = {
    "padding": "8px 10px", "textAlign": "left",
    "fontSize": "0.68rem", "fontWeight": "700",
    "color": "#94a3b8", "letterSpacing": "0.06em", "whiteSpace": "nowrap",
}
TH_CENTER = {**TH, "textAlign": "center"}
TH_STAT = {**TH, "textAlign": "center", "width": "50px", "minWidth": "50px", "maxWidth": "50px", "whiteSpace": "normal", "lineHeight": "1.2"}
TD = {
    "padding": "9px 10px", "fontSize": "0.82rem",
    "verticalAlign": "middle", "whiteSpace": "nowrap",
}
TD_CENTER = {**TD, "textAlign": "center"}
TD_STAT = {**TD, "textAlign": "center", "width": "50px", "minWidth": "50px", "maxWidth": "50px", "whiteSpace": "normal"}
PERCENTILE_STYLE = {**TD_CENTER, "fontSize": "0.75rem", "color": "#94a3b8"}

def percentile_cell(val, cell_style=None):
    base = {**TD_STAT, "fontWeight": "600", "fontSize": "0.75rem"}
    if cell_style:
        base.update(cell_style)
    v = str(val).strip().replace("%", "")
    try:
        pct = max(0.0, min(1.0, float(v) / 100.0))
        if pct >= 0.5:
            t = (pct - 0.5) * 2
            r = int(255 + (249 - 255) * t)
            g = int(255 + (115 - 255) * t)
            b = int(255 + (22  - 255) * t)
        else:
            t = pct * 2
            r = int(59  + (255 - 59)  * t)
            g = int(130 + (255 - 130) * t)
            b = int(246 + (255 - 246) * t)
        text_color = "#1e293b" if 0.35 <= pct <= 0.65 else "white"
        return html.Td(val, style={
            **base, "backgroundColor": f"rgb({r},{g},{b})",
            "color": text_color,
        })
    except:
        return html.Td(val, style={**TD_STAT, "fontSize": "0.75rem", "color": "#94a3b8"})

# ─────────────────────────────────────────────────────────────────────────────
# Column definitions
# (key, label, style, sortable, is_percentile)
# ─────────────────────────────────────────────────────────────────────────────
COL_GROUPS = [
    ("INFO",        6),
    ("USAGE",       3),
    ("EXTRA POSS",  4),
    ("SHOOTING",    4),
    ("EVANMIYA",    8),
]

COLS = [
    # key,                    label,               th_style,    is_pct
    ("status",                "STATUS",             TH,          False),
    ("player",                "PLAYER",             TH,          False),
    ("class",                 "CLASS",              TH,          False),
    ("size",                  "SIZE",               TH,          False),
    ("position",              "POS",                TH_CENTER,   False),
    ("current_team",          "CURRENT TEAM",       TH,          False),
    ("gs",                    "GS",                 TH_CENTER,   False),
    ("gp",                    "GP",                 TH_CENTER,   False),
    ("mp",                    "MP",                 TH_CENTER,   False),
    ("extra_poss",            "EXTRA POSS",         TH_STAT,     False),
    ("extra_poss_pct",        "%ILE",               TH_STAT,     True),
    ("extra_poss_per_min",    "EXTRA POSS/40",      TH_STAT,     False),
    ("extra_poss_per_min_pct","%ILE",               TH_STAT,     True),
    ("three_par",             "3PAR",               TH_STAT,     False),
    ("three_par_pct",         "%ILE",               TH_STAT,     True),
    ("three_p",               "3P%",                TH_STAT,     False),
    ("three_p_pct",           "%ILE",               TH_STAT,     True),
    ("obpr",                  "OBPR",               TH_STAT,     False),
    ("obpr_pct",              "%ILE",               TH_STAT,     True),
    ("dbpr",                  "DBPR",               TH_STAT,     False),
    ("dbpr_pct",              "%ILE",               TH_STAT,     True),
    ("bpr",                   "BPR",                TH_STAT,     False),
    ("bpr_pct",               "%ILE",               TH_STAT,     True),
    ("em_position",           "POSITION",           TH_STAT,     False),
    ("em_role",               "ROLE",               TH_STAT,     False),
]

# ─────────────────────────────────────────────────────────────────────────────
# Sorting helper
# ─────────────────────────────────────────────────────────────────────────────
def sort_key(val):
    v = str(val).strip().replace("%", "")
    try:    return (0, float(v))
    except: return (1, v.lower())

# ─────────────────────────────────────────────────────────────────────────────
# Table builder
# ─────────────────────────────────────────────────────────────────────────────
STATUS_ORDER = {"ENTERED": 0, "POTENTIAL": 1, "COMMITTED": 2, "WITHDRAWN": 3}

# ─────────────────────────────────────────────────────────────────────────────
# Column tooltips
# ─────────────────────────────────────────────────────────────────────────────
COL_TOOLTIPS = {
    "extra_poss":            "Extra Possessions generated by a player : OREB + DREB + STL - TOV",
    "extra_poss_pct":        "Percentile Rank for Extra Possessions",
    "extra_poss_per_min":    "Extra Possessions generated per 40 minutes played",
    "extra_poss_per_min_pct":"Percentile Rank for Extra Possessions per 40 minutes",
    "three_par":             "3-Point Attempt Rate",
    "three_par_pct":         "Percentile rank for 3-Point Attempt Rate",
    "three_p":               "3-Point Percentage",
    "three_p_pct":           "Percentile rank for 3-Point Percentage",
    "obpr":                  "Offensive Bayesian Performance Rating (from EvanMiya.com)",
    "obpr_pct":              "Percentile rank for Offensive Bayesian Performance Rating",
    "dbpr":                  "Defensive Bayesian Performance Rating (from EvanMiya.com)",
    "dbpr_pct":              "Percentile rank for Defensive Bayesian Performance Rating",
    "bpr":                   "Bayesian Performance Rating (from EvanMiya.com)",
    "bpr_pct":               "Percentile rank for Bayesian Performance Rating",
    "em_position":           "An estimate of a player's position based on his individual stats and team contributions. 1 corresponds to a Point Guard and 5 to a Center. (from EvanMiya.com)",
    "em_role":               "An estimate of a player's role based on his individual stats and team contributions. 1 corresponds to a Creator and 5 to a Receiver. (from EvanMiya.com)",
}

_TOOLTIP_STYLE = {
    "visibility": "hidden", "opacity": "0",
    "backgroundColor": "#1e293b", "color": "white",
    "fontSize": "0.72rem", "fontWeight": "400",
    "lineHeight": "1.4", "textAlign": "left",
    "borderRadius": "6px", "padding": "8px 10px",
    "position": "absolute", "zIndex": "100",
    "width": "220px", "top": "calc(100% + 6px)", "left": "50%",
    "transform": "translateX(-50%)",
    "boxShadow": "0 4px 12px rgba(0,0,0,0.15)",
    "transition": "opacity 0.15s",
    "pointerEvents": "none",
    "whiteSpace": "normal",
}

# Pre-build static group header row (never changes)
_GROUP_HEADER_ROW = html.Tr([
    html.Th(label, colSpan=span, style={
        **TH, "textAlign": "center", "borderBottom": "1px solid #e2e8f0",
        "color": "#cbd5e1" if not label else "#94a3b8",
        "paddingBottom": "4px", "fontSize": "0.6rem", "letterSpacing": "0.1em",
    })
    for label, span in COL_GROUPS
])

# Pre-compute per-column base th styles (reused every render)
_COL_BASE_STYLES = {
    key: {**th_style, "cursor": "pointer", "userSelect": "none"}
    for key, _, th_style, _ in COLS
}

def build_header(sort_col, sort_asc):
    col_headers = []
    for key, label, _, _ in COLS:
        arrow = (" ▲" if sort_asc else " ▼") if sort_col == key else ""
        base = _COL_BASE_STYLES[key]
        tooltip_text = COL_TOOLTIPS.get(key)

        inner_children = [html.Span(label + arrow)]
        if tooltip_text:
            inner_children.append(html.Span(tooltip_text, className="portal-tooltip", style=_TOOLTIP_STYLE))

        col_headers.append(html.Th(
            html.Div(inner_children,
                style={"display": "flex", "alignItems": "center", "position": "relative",
                       "justifyContent": base.get("textAlign", "left"),
                       "gap": "2px", "cursor": "pointer"}),
            id={"type": "portal-sort-col", "key": key},
            style={**base, "color": "#2563eb" if sort_col == key else base.get("color", "#94a3b8"),
                   "position": "relative", "overflow": "visible"},
        ))
    return html.Thead([
        _GROUP_HEADER_ROW,
        html.Tr(col_headers, style={"borderBottom": "2px solid #e2e8f0"}),
    ])

# Pre-compute player style (bold name cell reused)
_TD_PLAYER = {**TD, "fontWeight": "600"}

def build_table(players, sort_col=None, sort_asc=False):
    # Sort
    if sort_col:
        def row_sort_key(p):
            v = str(p.get(sort_col, "")).strip().replace("%", "")
            if v in ("", "-", "nan", "NaN"):
                return (1, 0)
            try:
                f = float(v)
                return (0, -f if not sort_asc else f)
            except:
                return (0, v.lower())
        players = sorted(players, key=row_sort_key)
    else:
        players = sorted(players, key=lambda p: STATUS_ORDER.get(p.get("status", "").upper(), 99))

    header = build_header(sort_col, sort_asc)

    # Rows
    if not players:
        body = html.Tbody([html.Tr([html.Td(
            html.Div([
                html.Div("📋", style={"fontSize": "2rem", "marginBottom": "8px"}),
                html.Div("No players match your filters", style={"fontWeight": "600", "color": "#475569"}),
            ], style={"textAlign": "center", "padding": "40px 0"}),
            colSpan=len(COLS), style={"textAlign": "center"},
        )])])
    else:
        rows = []
        for p in players:
            rows.append(html.Tr([
                html.Td(status_badge(p.get("status", "")),       style=TD),
                html.Td(p.get("player", ""),                     style=_TD_PLAYER),
                html.Td(p.get("class", ""),                      style=TD),
                html.Td(p.get("size", ""),                       style=TD),
                html.Td(p.get("position", ""),                   style=TD_CENTER),
                html.Td(p.get("current_team", ""),               style=TD),
                html.Td(p.get("gs", "—"),                        style=TD_CENTER),
                html.Td(p.get("gp", "—"),                        style=TD_CENTER),
                html.Td(p.get("mp", "—"),                        style=TD_CENTER),
                html.Td(p.get("extra_poss", "—"),                style=TD_STAT),
                percentile_cell(p.get("extra_poss_pct", "—")),
                html.Td(p.get("extra_poss_per_min", "—"),        style=TD_STAT),
                percentile_cell(p.get("extra_poss_per_min_pct","—")),
                html.Td(p.get("three_par", "—"),                 style=TD_STAT),
                percentile_cell(p.get("three_par_pct", "—")),
                html.Td(p.get("three_p", "—"),                   style=TD_STAT),
                percentile_cell(p.get("three_p_pct", "—")),
                html.Td(p.get("obpr", "—"),                      style=TD_STAT),
                percentile_cell(p.get("obpr_pct", "—")),
                html.Td(p.get("dbpr", "—"),                      style=TD_STAT),
                percentile_cell(p.get("dbpr_pct", "—")),
                html.Td(p.get("bpr", "—"),                       style=TD_STAT),
                percentile_cell(p.get("bpr_pct", "—")),
                html.Td(p.get("em_position", "—"),               style=TD_STAT),
                html.Td(p.get("em_role", "—"),                   style=TD_STAT),
            ], style={"borderBottom": "1px solid #f1f5f9", "transition": "background 0.15s", "cursor": "pointer"},
               className="portal-row"))
        body = html.Tbody(rows)

    return html.Div(
        html.Table([header, body], style={"width": "100%", "borderCollapse": "collapse"}),
        style={"overflowX": "auto"},
    )

# ─────────────────────────────────────────────────────────────────────────────
# Filter bar
# ─────────────────────────────────────────────────────────────────────────────
DROPDOWN_STYLE = {"fontSize": "0.78rem", "minWidth": "140px"}

def filter_bar():
    return html.Div([
        dcc.Dropdown(id="portal-filter-status",
            options=[{"label": v, "value": v} for v in unique_vals("status")],
            multi=True, placeholder="STATUS", style=DROPDOWN_STYLE),
        dcc.Dropdown(id="portal-filter-position",
            options=[{"label": v, "value": v} for v in unique_vals("position")],
            multi=True, placeholder="POSITION", style=DROPDOWN_STYLE),
        dcc.Dropdown(id="portal-filter-class",
            options=[{"label": v, "value": v} for v in unique_vals("class")],
            multi=True, placeholder="CLASS", style=DROPDOWN_STYLE),
        dcc.Dropdown(id="portal-filter-team",
            options=[{"label": v, "value": v} for v in unique_vals("current_team")],
            multi=True, placeholder="CURRENT TEAM", style={"fontSize": "0.78rem", "minWidth": "180px"}),
        dcc.Input(id="portal-filter-player", type="text", placeholder="SEARCH PLAYER...",
            debounce=True, style={
                "fontSize": "0.78rem", "padding": "6px 10px",
                "border": "1px solid #e2e8f0", "borderRadius": "6px",
                "width": "160px", "outline": "none",
            }),
    ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "alignItems": "center",
              "marginBottom": "16px", "padding": "16px", "backgroundColor": "white",
              "border": "1px solid #e2e8f0", "borderRadius": "10px"})

# ─────────────────────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────────────────────
def layout():
    return html.Div([
        html.Div(id="portal-tooltip-css", style={"display": "none"}),
        html.Div([
            html.Div([
                html.H2("PORTAL", style={"margin": 0, "fontWeight": "800"}),
                html.P("Transfer portal tracker · NCAA",
                       style={"color": "#94a3b8", "margin": "2px 0 0", "fontSize": "0.9rem"}),
            ]),
            html.Div(id="portal-summary", children=[]),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"}),

        # Filters
        filter_bar(),

        # Sort state store
        dcc.Store(id="portal-sort-state", data={"col": None, "asc": True}),

        # Table
        html.Div(
            build_table(PORTAL_PLAYERS),
            id="portal-table-container",
            style={"backgroundColor": "white", "border": "1px solid #e2e8f0",
                   "borderRadius": "10px", "padding": "8px 0", "overflowX": "auto"},
        ),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# Callbacks
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("portal-sort-state", "data"),
    Input({"type": "portal-sort-col", "key": ALL}, "n_clicks"),
    State("portal-sort-state", "data"),
    prevent_initial_call=True,
)
def update_sort(n_clicks, sort_state):
    triggered = callback_context.triggered[0]["prop_id"]
    key = json.loads(triggered.split(".")[0])["key"]
    if sort_state["col"] == key:
        return {"col": key, "asc": not sort_state["asc"]}
    return {"col": key, "asc": False}


@app.callback(
    Output("portal-table-container", "children"),
    Output("portal-summary", "children"),
    Input("portal-sort-state",      "data"),
    Input("portal-filter-status",   "value"),
    Input("portal-filter-position", "value"),
    Input("portal-filter-class",    "value"),
    Input("portal-filter-team",     "value"),
    Input("portal-filter-player",   "value"),
)
def update_table(sort_state, f_status, f_position, f_class, f_team, f_player):
    players = PORTAL_PLAYERS

    if f_status:
        players = [p for p in players if p["status"] in f_status]
    if f_position:
        players = [p for p in players if p["position"] in f_position]
    if f_class:
        players = [p for p in players if p["class"] in f_class]
    if f_team:
        players = [p for p in players if p["current_team"] in f_team]
    if f_player:
        players = [p for p in players if f_player.lower() in p["player"].lower()]

    sort_col = sort_state.get("col") if sort_state else None
    sort_asc = sort_state.get("asc", True) if sort_state else True

    # Build status summary
    counts = {}
    for p in players:
        s = p.get("status", "POTENTIAL")
        counts[s] = counts.get(s, 0) + 1

    summary_chips = []
    for status in ["ENTERED", "POTENTIAL", "COMMITTED", "WITHDRAWN"]:
        n = counts.get(status, 0)
        if n == 0 and status in ("ENTERED", "POTENTIAL"):
            continue
        bg, color, border = STATUS_STYLES.get(status, ("#f8fafc", "#475569", "#cbd5e1"))
        summary_chips.append(html.Span(
            [html.Strong(str(n), style={"marginRight": "5px"}), status],
            style={
                "backgroundColor": bg, "color": color,
                "border": f"1px solid {border}", "borderRadius": "6px",
                "padding": "6px 14px", "fontSize": "0.85rem", "fontWeight": "600",
            }
        ))

    summary = html.Div(summary_chips, style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap", "justifyContent": "flex-end"})

    return build_table(players, sort_col=sort_col, sort_asc=sort_asc), summary