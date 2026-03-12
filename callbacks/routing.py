from dash import Input, Output
from app import app
from data.db import get_conferences_by_tier
from layout import SIDEBAR_STYLE  # ← change components.layout to layout
import pages.home
import pages.team_rankings
import pages.player_rankings
import pages.hc_jobs
import pages.conf_brackets
import pages.teams_resume
import pages.coaches_challenges
import pages.portal

# ─────────────────────────────────────────────────────────────────────────────
# Page routing
# ─────────────────────────────────────────────────────────────────────────────
ROUTES = {
    "/":                   pages.home.layout,
    "/team-rankings":      pages.team_rankings.layout,
    "/player-rankings":    pages.player_rankings.layout,
    "/hc-jobs":            pages.hc_jobs.layout,
    "/conf-brackets":      pages.conf_brackets.layout,
    "/teams-resume":       pages.teams_resume.layout,
    "/coaches-challenges": pages.coaches_challenges.layout,
    "/portal":             pages.portal.layout,
}

# Pages that should hide the sidebar
NO_SIDEBAR_PAGES = {"/", "/hc-jobs", "/conf-brackets", "/portal"}


@app.callback(
    Output("page-content", "children"),
    Output("page-content", "style"),
    Output("sidebar", "style"),
    Input("url", "pathname"),
)
def render_page(pathname):
    page_fn = ROUTES.get(pathname, pages.home.layout)
    content = page_fn()

    if pathname in NO_SIDEBAR_PAGES:
        sidebar_style = {"display": "none"}
        content_style = {"marginLeft": "0", "marginTop": "52px", "padding": "1.5rem"}
    else:
        sidebar_style = SIDEBAR_STYLE
        content_style = {"marginLeft": "260px", "marginTop": "52px", "padding": "1.5rem"}

    return content, content_style, sidebar_style


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar filter callbacks
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(Output("conferences", "value"), Input("tier", "value"))
def update_conferences_from_tier(tier):
    if tier and tier != "All":
        return get_conferences_by_tier(tier)
    return []
