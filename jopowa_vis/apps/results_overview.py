import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd

from jopowa_vis.app import app, results_directory, config
from jopowa_vis.apps import plots

form = dbc.Row(
    [
        dbc.Col(
            [
                dbc.FormGroup(
                    [
                        dbc.Label("Select Scenario Set"),
                        dcc.Dropdown(
                            id="directory-select-id", className="mb-3"
                        ),
                    ]
                )
            ],
            width=3,
        )
    ]  # ,  justify="between"
)

energy = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dcc.Graph(
                                    id="supply_demand_aggr_graph_all",
                                    figure={},
                                )
                            ],
                            width="auto",
                        )
                    ],
                    justify="center",
                )
            ]
        )
    ]
)

capacities = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [dcc.Graph(id="results-capacity-plot", figure={})],
                            width="auto",
                        )
                    ],
                    justify="center",
                )
            ]
        )
    ]
)


layout = html.Div([form, energy, capacities])


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
            if s.endswith(".csv") and s != "capacity.csv"
        ]
        if scenarios:
            plot = plots.aggregated_supply_demand(dir, scenarios)
            plot["layout"].update({"width": 1000, "height": 700})
            return plot
        else:
            return plots.empty_plot("")


@app.callback(
    Output("results-capacity-plot", "figure"),
    [Input("directory-select-id", "value")],
)
def result_capacity_plot(scenario_directory):
    if scenario_directory is None:
        return plots.empty_plot("")
    else:
        file = os.path.join(
            results_directory, scenario_directory, "capacity.csv"
        )
        df = pd.read_csv(file).set_index("Technology")
        df = df.reindex(sorted(df.columns), axis=1)
        plot = plots.stacked_capacity_plot(df, config)
        plot["layout"].update({"width": 1000, "height": 700})
        return plot
