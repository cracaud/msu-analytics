from dash import html, dcc, Input, Output, ALL, callback_context, clientside_callback
import json
from app import app

# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────
from data.db import get_team_logo


# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────
CONF_BRACKETS = {
    "MVC": {
        "name": "MVC — Arch Madness",
        "round_labels": ["1ST ROUND", "QUARTER-FINAL", "SEMI-FINAL", "FINAL"],
        "rounds": [
            [
                {"id":"mvc-g1","t1":{"seed":8,"name":"Southern Illinois","score":63},"t2":{"seed":9, "name":"Drake","score":67},            "winner":2,"weight":1},
                {"id":"mvc-g2","t1":{"seed":7,"name":"Valparaiso","score":63},       "t2":{"seed":10,"name":"Indiana State","score":62},       "winner":1,"weight":1},
                {"id":"mvc-g3","t1":{"seed":6,"name":"Northern Iowa","score":68},    "t2":{"seed":11,"name":"Evansville","score":59},           "winner":1,"weight":1},
            ],
            [
                {"id":"mvc-g4","t1":{"seed":1,"name":"Belmont","score":79},    "t2":{"seed":9,"name":"Drake","score":100},       "winner":2,"weight":1},
                {"id":"mvc-g5","t1":{"seed":4,"name":"Murray State","score":79},"t2":{"seed":5,"name":"UIC","score":92},           "winner":2,"weight":1},
                {"id":"mvc-g6","t1":{"seed":2,"name":"Bradley","score":90},    "t2":{"seed":7,"name":"Valparaiso","score":84},     "winner":1,"weight":1},
                {"id":"mvc-g7","t1":{"seed":3,"name":"Illinois State"},   "t2":{"seed":6,"name":"Northern Iowa"},  "winner":None,"weight":1},
            ],
            [
                {"id":"mvc-g8", "t1":{"seed":9,"name":"Drake"},   "t2":{"seed":5,"name":"UIC"},     "winner":None,"weight":2},
                {"id":"mvc-g9", "t1":{"seed":2,"name":"Bradley"}, "t2":{"seed":None,"name":"W. G7"}, "winner":None,"weight":2},
            ],
            [
                {"id":"mvc-g10","t1":{"seed":None,"name":"W. G8"}, "t2":{"seed":None,"name":"W. G9"}, "winner":None,"weight":4},
            ],
        ],
        "spacers": { 0: [(0, 1)] },  # after G1 in R0, insert a bye spacer
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────
TEAM_BASE   = {"display":"flex","alignItems":"center","gap":"6px","padding":"5px 8px",
               "borderRadius":"5px","border":"1px solid #e2e8f0","background":"#fff",
               "fontSize":"0.72rem","cursor":"pointer","whiteSpace":"nowrap","width":"175px"}
TEAM_WINNER = {**TEAM_BASE,"background":"#eff6ff","borderColor":"#93c5fd","fontWeight":"700","color":"#1d4ed8"}
TEAM_LOSER  = {**TEAM_BASE,"opacity":"0.35"}
SEED_STYLE  = {"fontSize":"0.6rem","color":"#94a3b8","fontWeight":"700","minWidth":"14px"}
SCORE_STYLE = {"marginLeft":"auto","fontSize":"0.65rem","fontWeight":"700","color":"#475569"}
LOGO_STYLE  = {"height":"16px","width":"16px","objectFit":"contain"}
RND_LABEL   = {"fontSize":"0.6rem","fontWeight":"700","color":"#94a3b8",
               "letterSpacing":"0.08em","marginBottom":"6px","textAlign":"center"}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def seed_str(t):
    s = t.get("seed")
    return str(s) if s is not None else ""


def team_logo(name):
    """Fetch logo URL from DB; returns an Img element or None."""
    url = get_team_logo(name)
    if url:
        return html.Img(src=url, style=LOGO_STYLE)
    return None


def team_row(team, score, style):
    """Render a single team row inside a matchup card."""
    logo = team_logo(team["name"])
    children = [html.Span(seed_str(team), style=SEED_STYLE)]
    if logo is not None:
        children.append(logo)
    children.append(html.Span(team["name"]))
    children.append(html.Span(str(score) if score is not None else "", style=SCORE_STYLE))
    return html.Div(children, style=style)


def matchup_card(game):
    w  = game.get("winner")
    s1 = game.get("s1") or game["t1"].get("score")
    s2 = game.get("s2") or game["t2"].get("score")

    def sty(slot):
        if w is not None:
            return TEAM_WINNER if w == slot else TEAM_LOSER
        return TEAM_BASE

    return html.Div([
        team_row(game["t1"], s1, sty(1)),
        team_row(game["t2"], s2, sty(2)),
    ], id=game["id"], style={"display":"flex","flexDirection":"column","gap":"2px"})


def champion_box(name="TBD"):
    return html.Div([
        html.Div("🏆", style={"fontSize":"1.6rem"}),
        html.Div("CHAMPION", style={"fontSize":"0.55rem","letterSpacing":"0.1em",
                                    "opacity":"0.8","marginTop":"6px"}),
        html.Div(name, style={"fontSize":"0.85rem","fontWeight":"800","marginTop":"4px"}),
    ], style={"background":"linear-gradient(135deg,#1e3a5f,#2563eb)","color":"white",
              "borderRadius":"10px","padding":"16px 20px","textAlign":"center","minWidth":"100px"})


# ─────────────────────────────────────────────────────────────────────────────
# Bracket renderer
# ─────────────────────────────────────────────────────────────────────────────
def build_conf_bracket(conf, picks):
    data    = CONF_BRACKETS[conf]
    rounds  = data["rounds"]
    labels  = data["round_labels"]
    spacers = data.get("spacers", {})

    round_cols = []
    for r_idx, (games, label) in enumerate(zip(rounds, labels)):
        round_spacers = {after_idx: w for after_idx, w in spacers.get(r_idx, [])}

        items = []
        for g_idx, game in enumerate(games):
            items.append((game["weight"], matchup_card(game)))
            if g_idx in round_spacers:
                items.append((round_spacers[g_idx], None))

        slots = []
        for weight, content in items:
            if content is None:
                slots.append(html.Div(style={"flex": str(weight), "minHeight": "0"}))
            else:
                slots.append(html.Div(content, style={
                    "flex":           str(weight),
                    "display":        "flex",
                    "alignItems":     "center",
                    "justifyContent": "center",
                    "paddingRight":   "10px",
                    "minHeight":      "0",
                }))

        round_cols.append(html.Div([
            html.Div(label, style=RND_LABEL),
            html.Div(slots, style={
                "display": "flex", "flexDirection": "column",
                "flex": "1", "minHeight": "0",
            }),
        ], style={
            "display": "flex", "flexDirection": "column",
            "minWidth": "215px", "flexShrink": "0",
        }))

    # Champion column
    round_cols.append(html.Div([
        html.Div("", style={**RND_LABEL, "visibility": "hidden"}),
        html.Div([
            html.Div("→", style={"fontSize":"1rem","color":"#cbd5e1","marginRight":"8px"}),
            champion_box(),
        ], style={"flex":"1","display":"flex","alignItems":"center","minHeight":"0"}),
    ], style={"display":"flex","flexDirection":"column","flexShrink":"0"}))

    return html.Div([
        # SVG container for connector lines (populated by clientside_callback)
        html.Div(id="bracket-svg-container", style={
            "position":"absolute","top":"0","left":"0",
            "width":"100%","height":"100%","pointerEvents":"none",
        }),
        # Bracket columns
        html.Div(round_cols, style={
            "display":"flex","flexDirection":"row","alignItems":"stretch",
            "height":"380px","overflowX":"auto","padding":"8px 4px",
        }),
    ], id="bracket-canvas", style={"position":"relative"})


# ─────────────────────────────────────────────────────────────────────────────
# Clientside callback — draws SVG connector lines after render
# Triggered by a one-shot Interval that fires 150ms after page load/update
# ─────────────────────────────────────────────────────────────────────────────
clientside_callback(
    """
    function(n) {
        if (!n) return false;

        var edges = [
            ['mvc-g1','mvc-g4'], ['mvc-g2','mvc-g6'], ['mvc-g3','mvc-g7'],
            ['mvc-g4','mvc-g8'], ['mvc-g5','mvc-g8'],
            ['mvc-g6','mvc-g9'], ['mvc-g7','mvc-g9'],
            ['mvc-g8','mvc-g10'], ['mvc-g9','mvc-g10']
        ];

        var canvas    = document.getElementById('bracket-canvas');
        var container = document.getElementById('bracket-svg-container');
        if (!canvas || !container) return false;

        container.innerHTML = '';
        var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width',  canvas.offsetWidth);
        svg.setAttribute('height', canvas.offsetHeight);
        svg.style.position = 'absolute';
        svg.style.top  = '0';
        svg.style.left = '0';
        svg.style.overflow = 'visible';
        container.appendChild(svg);

        var cr = canvas.getBoundingClientRect();
        function midY(el) { var r = el.getBoundingClientRect(); return r.top + r.height/2 - cr.top; }
        function rx(el)   { return el.getBoundingClientRect().right - cr.left; }
        function lx(el)   { return el.getBoundingClientRect().left  - cr.left; }

        var dstGroups = {};
        edges.forEach(function(e) {
            if (!dstGroups[e[1]]) dstGroups[e[1]] = [];
            dstGroups[e[1]].push(e[0]);
        });

        edges.forEach(function(edge) {
            var src = document.getElementById(edge[0]);
            var dst = document.getElementById(edge[1]);
            if (!src || !dst) return;

            var x1 = rx(src), y1 = midY(src);
            var x2 = lx(dst), y2 = midY(dst);
            var mx = (x1 + x2) / 2;

            var mergeY = y2;
            var srcs = dstGroups[edge[1]];
            if (srcs.length === 2) {
                var otherId = srcs.filter(function(s){ return s !== edge[0]; })[0];
                var other   = document.getElementById(otherId);
                if (other) mergeY = (midY(src) + midY(other)) / 2;
            }

            var pts  = x1+','+y1+' '+mx+','+y1+' '+mx+','+mergeY+' '+x2+','+y2;
            var line = document.createElementNS('http://www.w3.org/2000/svg','polyline');
            line.setAttribute('points',          pts);
            line.setAttribute('fill',            'none');
            line.setAttribute('stroke',          '#cbd5e1');
            line.setAttribute('stroke-width',    '2');
            line.setAttribute('stroke-linejoin', 'round');
            svg.appendChild(line);
        });

        return true;  // disable the interval
    }
    """,
    Output("bracket-draw-interval", "disabled", allow_duplicate=True),
    Input("bracket-draw-interval",  "n_intervals"),
    prevent_initial_call=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Tabs + layout
# ─────────────────────────────────────────────────────────────────────────────
CONF_LIST = list(CONF_BRACKETS.keys())
ALL_TABS  = CONF_LIST


def tab_bar(active):
    return html.Div([
        html.Div(t, id={"type":"bracket-tab","name":t}, style={
            "padding":"8px 18px","cursor":"pointer",
            "fontSize":"0.75rem","fontWeight":"700","letterSpacing":"0.06em",
            "borderBottom":"3px solid #2563eb" if t == active else "3px solid transparent",
            "color":"#2563eb" if t == active else "#64748b",
        }) for t in ALL_TABS
    ], style={"display":"flex","borderBottom":"1px solid #e2e8f0","marginBottom":"20px","gap":"4px"})


def layout():
    return html.Div([
        html.Div([
            html.H2("BRACKETS", style={"margin":0,"fontWeight":"800"}),
            html.P("Conference tournaments",
                   style={"color":"#94a3b8","margin":"2px 0 0","fontSize":"0.9rem"}),
        ], style={"marginBottom":"24px"}),
        dcc.Store(id="bracket-active-tab", data=CONF_LIST[0]),
        dcc.Store(id="bracket-picks",      data={}),
        # Fires 150ms after render to trigger SVG line drawing
        dcc.Interval(id="bracket-draw-interval", interval=150, max_intervals=1, disabled=False),
        html.Div(id="bracket-tabs-bar"),
        html.Div(id="bracket-content"),
    ])


@app.callback(
    Output("bracket-active-tab", "data"),
    Input({"type":"bracket-tab","name":ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def switch_tab(n_clicks):
    triggered = callback_context.triggered[0]["prop_id"]
    return json.loads(triggered.split(".")[0])["name"]


@app.callback(
    Output("bracket-tabs-bar",      "children"),
    Output("bracket-content",       "children"),
    Output("bracket-draw-interval", "disabled", allow_duplicate=True),
    Input("bracket-active-tab",     "data"),
    Input("bracket-picks",          "data"),
    prevent_initial_call='initial_duplicate',
)
def render_bracket(active_tab, picks):
    picks   = picks or {}
    tabs    = tab_bar(active_tab)
    content = build_conf_bracket(active_tab, picks)
    return tabs, html.Div(content, style={
        "backgroundColor":"white","border":"1px solid #e2e8f0",
        "borderRadius":"10px","padding":"20px","overflowX":"auto",
    }), False  # re-enable interval so it fires after this render