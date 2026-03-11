from dash import html
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H2("🏃 Player Rankings"),
        html.Hr(),
        dbc.Alert("Coming soon — Player Rankings.", color="info"),
    ])
