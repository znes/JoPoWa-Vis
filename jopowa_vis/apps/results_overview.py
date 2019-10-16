import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from jopowa_vis.app import app, results_directory
from jopowa_vis.apps import plots

row = dbc.Row(
    [       dbc.FormGroup(
            [
                dbc.Label("Select Sceanrio Set"),
                dcc.Dropdown(
                    id="directory-select-id",
                    className="mb-3",
                ),
            ]
        ),
        dbc.Col([
            dcc.Graph(
                id="supply_demand_aggr_graph_all", figure={}
            )
        ]),
    ]
)

layout = html.Div([row])

@app.callback(
    Output("supply_demand_aggr_graph_all", "figure"),
    [
        Input("directory-select-id", "value"),
    ],
)
def display_aggregated_supply_demand_graph(directory):
    return {}

    # path = os.path.exists(os.path.join(results_directory, directory))
    # if os.path.exists(path):
    #     scenarios = os.path.listdir(path)
    #     return plots.aggregated_supply_demand(path, scenarios)
    # else:
    #     return {}


@app.callback(
    Output("directory-select-id", "options"),
    [Input("button", "columns")],
)
def update_scenario_select(columns):
    if columns is None:
        return None

    return [
        {"label": c["id"], "value": c["name"]}
        for c in columns
        if c["id"] != "Technology"
    ]
