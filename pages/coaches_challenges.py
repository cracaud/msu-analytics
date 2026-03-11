from dash import html
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H2("🎯 Coach's Challenges"),
        html.Hr(),
        dbc.Alert("Coming soon — Coach's Challenges.", color="info"),
    ])
