from dash import html
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H2("📊 Team Rankings"),
        html.Hr(),
        dbc.Alert("Coming soon — Team Rankings.", color="info"),
    ])
