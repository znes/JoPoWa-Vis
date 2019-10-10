import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


slider = dbc.Row(
    [
        dbc.Col(
            [
                dbc.FormGroup(
                    [
                        dbc.Label("Water Pumping", html_for="slider"),
                        dcc.Slider(
                            id="pumping_slider",
                            min=0,
                            max=10,
                            step=0.5,
                            value=3,
                        ),
                        dbc.Label("Water Desalination ", html_for="slider"),
                        dcc.Slider(
                            id="desalination_slider",
                            min=0,
                            max=10,
                            step=0.5,
                            value=3,
                        ),
                    ]
                )
            ]
        ),
        dbc.Col([]),
    ]
)

layout = html.Div([slider])
