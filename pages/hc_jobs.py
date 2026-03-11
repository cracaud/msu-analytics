from dash import html, dcc, Input, Output, State, ALL, callback_context
import json
import pandas as pd
import os
import dash_bootstrap_components as dbc
from app import app

# ─────────────────────────────────────────────────────────────────────────────
# Data — loaded from CSV
# ─────────────────────────────────────────────────────────────────────────────
RISK_ORDER = {"OPEN": 0, "HOT SEAT": 1, "ELEVATED": 2, "STABLE": 3, "VERY SAFE": 4}
RISK_SCORE = {"OPEN": 0, "HOT SEAT": 9, "ELEVATED": 6, "STABLE": 3, "VERY SAFE": 1}

def load_coaches():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "Coaches_Fired.csv")
    df = pd.read_csv(path).dropna(subset=["school"])
    df = df[df["school"].str.strip() != ""]
    coaches = []
    for _, row in df.iterrows():
        w = int(row["3yrs_W"]) if pd.notna(row["3yrs_W"]) else 0
        l = int(row["3yrs_L"]) if pd.notna(row["3yrs_L"]) else 0
        risk = str(row["firing_risk"]).strip().upper()
        is_open = risk == "OPEN"
        coaches.append({
            "name":          str(row["head_coach"]).strip(),
            "school":        str(row["school"]).strip(),
            "conference":    str(row["conference"]).strip(),
            "record":        f"{w}-{l}" if not is_open else "—",
            "expectations":  str(row["expectations"]).strip().title(),
            "risk":          RISK_SCORE.get(risk, 5),
            "risk_label":    risk,
            "hot_seat":      risk == "HOT SEAT",
            "open":          is_open,
            "contract_years": int(row["yrs_left"]) if pd.notna(row.get("yrs_left")) and str(row.get("yrs_left")).strip() != "" else None,
        })
    return coaches

COACHES = load_coaches()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def BADGE_STYLE(bg, color, border):
    return {
        "backgroundColor": bg,
        "color": color,
        "border": f"1px solid {border}",
        "borderRadius": "4px",
        "padding": "2px 8px",
        "fontSize": "0.75rem",
        "fontWeight": "700",
        "whiteSpace": "nowrap",
    }


def risk_badge(score):
    if score <= 3:
        return html.Span("VERY SAFE",  style=BADGE_STYLE("#f0fdf4", "#16a34a", "#86efac"))
    elif score <= 5:
        return html.Span("STABLE",     style=BADGE_STYLE("#f0fdf4", "#16a34a", "#86efac"))
    elif score <= 7:
        return html.Span("ELEVATED",   style=BADGE_STYLE("#fefce8", "#a16207", "#fde68a"))
    else:
        return html.Span("HOT SEAT",   style=BADGE_STYLE("#fef2f2", "#dc2626", "#fca5a5"))


def open_badge():
    return html.Span("OPEN", style=BADGE_STYLE("#fef2f2", "#dc2626", "#fca5a5"))


def win_pct(record):
    """Return formatted win percentage from 'W-L' string, or None if not applicable."""
    try:
        w, l = record.split("-")
        total = int(w) + int(l)
        return f"({int(w)/total:.3f})" if total > 0 else None
    except Exception:
        return None


def record_display(record):
    pct = win_pct(record)
    if pct:
        return html.Span([
            record,
            html.Span(f" {pct}", style={"color": "#94a3b8", "fontSize": "0.75rem"}),
        ])
    return html.Span(record)



    if val:
        return html.Span("YES", style={
            "backgroundColor": "#fef2f2", "color": "#dc2626",
            "border": "1px solid #fca5a5", "borderRadius": "4px",
            "padding": "2px 8px", "fontSize": "0.75rem", "fontWeight": "700",
        })
    return html.Span("NO", style={
        "backgroundColor": "#f0fdf4", "color": "#16a34a",
        "border": "1px solid #86efac", "borderRadius": "4px",
        "padding": "2px 8px", "fontSize": "0.75rem", "fontWeight": "700",
    })


def expectations_pill(val):
    colors = {
        "Elite":     ("#eff6ff", "#1d4ed8", "#bfdbfe"),
        "High":      ("#faf5ff", "#7c3aed", "#ddd6fe"),
        "Mid":       ("#fff7ed", "#c2410c", "#fed7aa"),
        "Mid-Major": ("#fff7ed", "#c2410c", "#fed7aa"),
        "Low":       ("#f8fafc", "#475569", "#cbd5e1"),
    }
    bg, color, border = colors.get(val, ("#f8fafc", "#475569", "#cbd5e1"))
    return html.Span(val, style={
        "backgroundColor": bg, "color": color,
        "border": f"1px solid {border}", "borderRadius": "4px",
        "padding": "2px 8px", "fontSize": "0.75rem", "fontWeight": "600",
    })


def build_table(coaches):
    header = html.Thead(html.Tr([
        html.Th("#",                  style=TH),
        html.Th("COACH",              style=TH),
        html.Th("SCHOOL",             style=TH),
        html.Th("CONFERENCE",         style=TH),
        html.Th("3-YR RECORD",        style=TH),
        html.Th("YRS LEFT",           style={**TH, "whiteSpace": "nowrap"}),
        html.Th("EXPECTATIONS",       style=TH),
        html.Th("FIRING RISK",        style={**TH, "textAlign": "center", "paddingRight": "24px"}),
    ], style={"borderBottom": "2px solid #e2e8f0"}))

    rows = []
    for i, c in enumerate(sorted(coaches, key=lambda x: (-x.get("open", False), -x["risk"]))):
        is_open = c.get("open", False)
        row_style = {
            "cursor": "pointer", "borderBottom": "1px solid #f1f5f9",
            "transition": "background 0.15s",
            **({"backgroundColor": "#fef2f2"} if is_open else {}),
        }
        rows.append(html.Tr([
            html.Td(i + 1, style={**TD, "color": "#94a3b8", "fontSize": "0.8rem"}),
            html.Td(
                html.Div([
                    html.Span("OPEN POSITION", style={"fontWeight": "700", "color": "#dc2626"}),
                    html.Span(f" · prev. {c['name']}", style={"fontSize": "0.65rem", "color": "#94a3b8", "marginLeft": "6px"}),
                ]) if is_open else html.Span(c["name"], style={"fontWeight": "600"}),
                style=TD,
            ),
            html.Td(c["school"],    style=TD),
            html.Td(c["conference"], style={**TD, "color": "#64748b"}),
            html.Td(record_display(c["record"]), style={**TD, "fontFamily": "monospace"}),
            html.Td(
                "—" if c["contract_years"] is None else f'{c["contract_years"]} yr{"s" if c["contract_years"] != 1 else ""}',
                style=TD
            ),
            html.Td(expectations_pill(c["expectations"]), style={**TD, "textAlign": "center"}),
            html.Td(open_badge() if is_open else risk_badge(c["risk"]), style={**TD, "textAlign": "center", "paddingRight": "24px"}),
        ], id={"type": "coach-row", "index": i},
           style=row_style,
           className="coach-row"
        ))

    return html.Div(
        html.Table([header, html.Tbody(rows)],
                   style={"width": "100%", "borderCollapse": "collapse"}),
        style={"paddingRight": "16px"}
    )


def build_detail_panel(coach):
    is_open = coach.get("open", False)
    score = coach["risk"]

    if is_open:
        bar_color, verdict = "#dc2626", "Position Open"
    elif score <= 3:
        bar_color, verdict = "#22c55e", "Safe"
    elif score <= 6:
        bar_color, verdict = "#f59e0b", "Watch List"
    else:
        bar_color, verdict = "#ef4444", "On The Hot Seat"

    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.H3(
                    "Open Position" if is_open else coach["name"],
                    style={"margin": 0, "fontWeight": "800", "fontSize": "1.4rem",
                           "color": "#dc2626" if is_open else "inherit"},
                ),
                html.Div(
                    f'{coach["school"]} · {coach["conference"]}' + (f'  ·  prev. {coach["name"]}' if is_open else ""),
                    style={"color": "#64748b", "fontSize": "0.9rem", "marginTop": "2px"},
                ),
            ]),
            html.Div(verdict, style={
                "backgroundColor": bar_color, "color": "white",
                "borderRadius": "6px", "padding": "4px 12px",
                "fontWeight": "700", "fontSize": "0.85rem",
                "alignSelf": "center",
            }),
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "20px"}),

        # Risk meter (hidden for open positions)
        *([
            html.Div([
                html.Div("FIRING RISK GRADE", style=LABEL),
                html.Div([
                    html.Div(style={
                        "height": "10px", "width": f'{score * 10}%',
                        "backgroundColor": bar_color, "borderRadius": "5px",
                        "transition": "width 0.4s ease",
                    }),
                ], style={"backgroundColor": "#f1f5f9", "borderRadius": "5px",
                          "height": "10px", "marginBottom": "4px"}),
                html.Div(f'{score} / 10', style={"fontWeight": "800", "fontSize": "1.5rem",
                                                  "color": bar_color}),
            ], style={"marginBottom": "20px"}),
        ] if not is_open else [
            html.Div([
                html.Div("STATUS", style=LABEL),
                html.Div("Actively searching for head coach",
                         style={"fontWeight": "600", "color": "#dc2626", "fontSize": "0.9rem"}),
            ], style={"marginBottom": "20px"}),
        ]),

        html.Hr(style={"borderColor": "#f1f5f9", "margin": "16px 0"}),

        # Stats grid
        html.Div([
            detail_stat("SCHOOL",           coach["school"]),
            detail_stat("CONFERENCE",       coach["conference"]),
            detail_stat("EXPECTATIONS",     coach["expectations"]),
            detail_stat("PREV. COACH",      coach["name"]) if is_open else detail_stat("3-YR RECORD", record_display(coach["record"])),
        ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"}),
    ], style={
        "backgroundColor": "white",
        "border": f'1px solid {"#fca5a5" if is_open else "#e2e8f0"}',
        "borderRadius": "10px",
        "padding": "24px",
        "position": "sticky",
        "top": "70px",
    })


def detail_stat(label, value):
    return html.Div([
        html.Div(label, style=LABEL),
        html.Div(value, style={"fontWeight": "700", "fontSize": "1rem"}),
    ], style={
        "backgroundColor": "#f8fafc",
        "borderRadius": "8px",
        "padding": "12px 14px",
    })


# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────
TH = {
    "padding": "10px 12px", "textAlign": "left",
    "fontSize": "0.7rem", "fontWeight": "700",
    "color": "#94a3b8", "letterSpacing": "0.06em",
}
TD = {
    "padding": "12px 12px", "fontSize": "0.875rem",
    "verticalAlign": "middle", "whiteSpace": "nowrap",
}
LABEL = {
    "fontSize": "0.68rem", "fontWeight": "700",
    "color": "#94a3b8", "letterSpacing": "0.06em",
    "marginBottom": "4px",
}

# ─────────────────────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────────────────────
def layout():
    return html.Div([
        # Page header
        html.Div([
            html.H2("JOBS", style={"margin": 0, "fontWeight": "800"}),
            html.P("Head Coach firing risk tracker · NCAA",
                   style={"color": "#94a3b8", "margin": "2px 0 0", "fontSize": "0.9rem"}),
        ], style={"marginBottom": "24px"}),

        # Body: table + detail panel
        html.Div([
            # Table
            html.Div(
                build_table(COACHES),
                id="jobs-table-container",
                style={
                    "backgroundColor": "white",
                    "border": "1px solid #e2e8f0",
                    "borderRadius": "10px",
                    "padding": "8px 0",
                    "overflowX": "auto",
                    "flex": "1",
                    "minWidth": "0",
                    "boxSizing": "border-box",
                }
            ),

            # Detail panel
            html.Div(
                id="jobs-detail-panel",
                style={"width": "300px", "minWidth": "300px", "flexShrink": "0"},
            ),
        ], style={"display": "flex", "gap": "20px", "alignItems": "flex-start", "overflowX": "hidden"}),

        # Store selected coach index
        dcc.Store(id="selected-coach-index", data=None),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("jobs-detail-panel", "children"),
    Input({"type": "coach-row", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def show_detail(n_clicks):
    if not callback_context.triggered:
        return None
    triggered = callback_context.triggered[0]["prop_id"]
    idx = json.loads(triggered.split(".")[0])["index"]
    sorted_coaches = sorted(COACHES, key=lambda x: (-x.get("open", False), -x["risk"]))
    return build_detail_panel(sorted_coaches[idx])