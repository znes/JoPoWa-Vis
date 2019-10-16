import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from jopowa_vis.app import app, results_directory
from jopowa_vis.apps import plots

row = dbc.Row(
    [
        dbc.FormGroup(
            [
                dbc.Label("Select Scenario Set"),
                dcc.Dropdown(id="directory-select-id", className="mb-3"),
                dbc.Button(
                    "Update list",
                    id="update-dirlist",
                    n_clicks=0,
                    color="secondary",
                ),
            ]
        ),
        dbc.Col([dcc.Graph(id="supply_demand_aggr_graph_all", figure={})]),
    ]
)

layout = html.Div([row])


@app.callback(
    Output("supply_demand_aggr_graph_all", "figure"),
    [Input("directory-select-id", "value")],
)
def display_aggregated_supply_demand_graph(scenario_directory):
    if scenario_directory is None:
        return plots.empty_plot("")
    else:
        dir = os.path.join(results_directory, scenario_directory)
        scenarios = [
            s.replace(".csv", "")
            for s in os.listdir(dir)
            if s.endswith(".csv")
        ]
        plot = plots.aggregated_supply_demand(dir, scenarios)
        plot["layout"].update({"width": 800})
        return plot

    # path = os.path.exists(os.path.join(results_directory, directory))
    # if os.path.exists(path):
    #     scenarios = os.path.listdir(path)
    #     return plots.aggregated_supply_demand(path, scenarios)
    # else:
    #     return {}


@app.callback(
    Output("directory-select-id", "options"),
    [Input("update-dirlist", "n_clicks")],
)
def update_dirlist_select(n_clicks):
    if n_clicks > 0:
        items = os.listdir(results_directory)

        return [
            {"label": i, "value": i}
            for i in items
            if os.path.isdir(os.path.join(results_directory, i))
        ]
    else:
        return []
