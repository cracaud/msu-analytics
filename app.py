from dash import Dash
import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
app.title = "Basketball Analytics"
server = app.server

import layout      # ← sets app.layout
import callbacks   # ← registers your callbacks

if __name__ == "__main__":
    app.run(debug=False)
