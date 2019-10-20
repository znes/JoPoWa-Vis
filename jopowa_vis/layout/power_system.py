import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import multiprocessing as mp
import pandas as pd

from jopowa_vis.app import app, results_directory, config
from jopowa_vis.apps import optimization, plots


# card for hourly production --------------------------------------------------
hourly_power_graph = dbc.Card(
    [
        dbc.CardHeader(["Hourly Power Supply and Demand"]),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                # ?
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.FormGroup(
                                    [
                                        dbc.Label("Select scenario"),
                                        dcc.Dropdown(
                                            id="scenario-select-id",
                                            className="mb-3",
                                        ),
                                    ]
                                )
                            ],
                            width={"size": 2, "order": "last"},
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dcc.Graph(
                                    id="hourly-production-graph", figure={}
                                )
                            ],
                            width={"size": 8, "order": "first"},
                        ),
                        dbc.Col(
                            [
                                dcc.Graph(
                                    id="supply_demand_aggr_graph", figure={}
                                )
                            ],
                            width="auto",
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        # dbc.Form(
                        #     [
                        #         dbc.FormGroup(
                        #             [
                        #                 dbc.Button(
                        #                     "Compute",
                        #                     id="open",
                        #                     color="primary",
                        #                     n_clicks=0,
                        #                 )
                        #             ]
                        #         )
                        #     ],
                        #     inline=True,
                        # )
                    ]
                ),
            ]
        ),
    ]
)

layout = html.Div([hourly_power_graph])




@app.callback(
    Output("hourly-production-graph", "figure"),
    [
        Input("scenario-table-technology", "data"),
        Input("scenario-select-id", "value"),
    ],
    [State("directory-select-id", "value")],
)
def display_hourly_graph(rows, scenario, scenario_set):
    """
    """
    if scenario is None:
        return plots.empty_plot("")

    elif os.path.exists(
        os.path.join(results_directory, scenario_set, scenario + ".csv")
    ):
        df = pd.read_csv(
            os.path.join(results_directory, scenario_set, scenario + ".csv"),
            parse_dates=True,
            index_col=0,
        )
        plot = plots.hourly_power_plot(df, scenario, config)
        plot["layout"].update({"width": 1000})
        return plot

    else:
        return plots.empty_plot("")


@app.callback(
    Output("supply_demand_aggr_graph", "figure"),
    [
        Input("scenario-table-technology", "data"),
        Input("scenario-select-id", "value"),
    ],
    [State("directory-select-id", "value")],
)
def display_aggregated_supply_demand_graph(data, scenario, scenario_set):
    if scenario == "" or scenario is None:
        return plots.empty_plot("")
    elif os.path.exists(
        os.path.join(results_directory, scenario_set, scenario + ".csv")
    ):
        dir = os.path.join(results_directory, scenario_set)
        plot = plots.aggregated_supply_demand(dir, [scenario], config)
        plot["layout"].update({"width": 500})
        return plot
    else:
        return plots.empty_plot("")
