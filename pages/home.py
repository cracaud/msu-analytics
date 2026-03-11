from dash import html
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H2("🏠 Home"),
        html.Hr(),
        dbc.Alert("Welcome to Basketball Analytics!", color="primary"),
    ])
