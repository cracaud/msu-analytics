from dash import html
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H2("📋 Teams Resume"),
        html.Hr(),
        dbc.Alert("Coming soon — Teams Resume.", color="info"),
    ])
