import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

# import dash_table

import pandas as pd
import plotly.graph_objs as go

from jopowa_vis.app import app, results_directory
from jopowa_vis.apps import calculations, optimization

# card for hourly production --------------------------------------------------
hourly_power_graph = dbc.Card(
    [
        dbc.CardHeader(["Hourly Power Supply and Demand"]),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [dcc.Graph(id="hourly-production-graph", figure={})],
                            width=8,
                        ),
                        dbc.Col(
                            [dcc.Graph(id="supply_demand_aggr_graph", figure={})],
                            width=4,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Button("Compute", id="open"),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader("Info"),
                                        dbc.ModalBody("Computation done."),
                                        dbc.ModalFooter(
                                            dbc.Button(
                                                "Close", id="close", className="ml-auto"
                                            )
                                        ),
                                    ],
                                    id="modal",
                                ),
                            ],
                            width={"order": "last", "width": 2, "style": "primary"},
                        )
                    ]
                ),
            ]
        ),
    ]
)

layout = html.Div([hourly_power_graph])


@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open"), State("scenario-select-id", "value")],
)
def toggle_modal(n1, n2, is_open, scenario):
    if scenario is not None:
        # optimization.compute(scenario)
        if n1 or n2:
            return not is_open
        else:
            return is_open


@app.callback(
    Output("hourly-production-graph", "figure"),
    [Input("scenario-table-technology", "data"), Input("scenario-select-id", "value")],
)
def display_hourly_graph(rows, scenario):
    """
    """
    layout = go.Layout(
        barmode="stack",
        title="Hourly supply and demand in for <br> scenario {}.".format(scenario),
        yaxis=dict(
            title="Energy in MWh",
            titlefont=dict(size=16, color="rgb(107, 107, 107)"),
            tickfont=dict(size=14, color="rgb(107, 107, 107)"),
        ),
        yaxis2=dict(
            title="Energy in MWh",
            overlaying="y",
            rangemode="tozero",
            autorange=True,
            side="right",
            showgrid=False,
        ),
    )

    data = []

    if scenario == "" or scenario is None:
        return {}

    elif os.path.exists(os.path.join(results_directory, scenario + ".csv")):
        df = pd.read_csv(
            os.path.join(results_directory, scenario + ".csv"),
            parse_dates=True,
            index_col=0,
        )

        for c in df.columns:
            if "demand" in c:
                data.append(
                    go.Scatter(
                        x=df.index,
                        y=df[c],
                        name=c,
                        line=dict(
                            width=3, color=app.color_dict.get(c.lower(), "black")
                        ),
                    )
                )
            elif c == "excess":
                data.append(
                    go.Scatter(
                        x=df.index,
                        y=df[c] * -1,
                        name=c,
                        stackgroup="negative",
                        line=dict(
                            width=0, color=app.color_dict.get(c.lower(), "black")
                        ),
                    )
                )
            elif "storage" in c:
                data.append(
                    go.Scatter(
                        x=df.index,
                        y=df[c].clip(lower=0),
                        name=c,
                        stackgroup="positive",
                        line=dict(
                            width=0, color=app.color_dict.get(c.lower(), "black")
                        ),
                        showlegend=True,
                    )
                )
                data.append(
                    go.Scatter(
                        x=df.index,
                        y=df[c].clip(upper=0),
                        name=c,
                        stackgroup="negative",
                        line=dict(
                            width=0, color=app.color_dict.get(c.lower(), "black")
                        ),
                        showlegend=False,
                    )
                )
            else:
                data.append(
                    go.Scatter(
                        x=df.index,
                        fillcolor=app.color_dict.get(c.lower(), "black"),
                        y=df[c].clip(lower=0),
                        name=c,
                        stackgroup="positive",
                        line=dict(
                            width=0, color=app.color_dict.get(c.lower(), "black")
                        ),
                    )
                )
        return {"data": data, "layout": layout}

    else:
        return {}


@app.callback(
    Output("supply_demand_aggr_graph", "figure"),
    [Input("scenario-table-technology", "data"), Input("scenario-select-id", "value")],
)
def display_aggregated_supply_demand_graph(data, scenario):
    if scenario == "" or scenario is None:
        return {}
    elif os.path.exists(os.path.join(results_directory, scenario + ".csv")):
        df = pd.read_csv(
            os.path.join(results_directory, scenario + ".csv"),
            parse_dates=True,
            index_col=0,
        )
        agg = df[df > 0].sum() / 1e6  # -> TWh
        agg[["demand", "excess"]] = agg[["demand", "excess"]].multiply(-1)
        agg["storage-consumption"] = df["storage"].clip(upper=0).sum() / 1e6  # -> TWh

        layout = go.Layout(
            barmode="relative",
            title="Aggregated Supply and demand for <br> {} scenario".format(scenario),
            width=400,
            yaxis=dict(
                title="Energy in TWh",
                titlefont=dict(size=16, color="rgb(107, 107, 107)"),
                tickfont=dict(size=14, color="rgb(107, 107, 107)"),
            ),
        )

        mapper = {"storage-consumption": "storage"}
        data = []

        for idx, row in agg.to_frame().T.iteritems():
            if idx == "storage-consumption":
                legend = False
            else:
                legend = True
            data.append(
                go.Bar(
                    x=row.index,
                    y=row.values,
                    text=[v.round(1) for v in row.values],
                    hovertext=[v.round(1) for v in row.values],
                    hoverinfo="text",
                    textposition="auto",
                    showlegend=legend,
                    name=mapper.get(idx, idx),
                    marker=dict(
                        color=app.color_dict.get(mapper.get(idx, idx).lower(), "gray")
                    ),
                )
            )

        return {"data": data, "layout": layout}

    else:
        df = pd.DataFrame(data)

        if scenario not in df.columns:
            return {}
        elif df[scenario].isnull().any():
            return {}

        df.set_index("Technology", inplace=True)

        timeseries = calculations.timeseries(df[scenario])

        agg = (timeseries.sum() / 1e6).drop(["RL"])  # MWh -> GWh
        # convert to negative for plotting

        agg[["Demand", "Excess"]] = agg[["Demand", "Excess"]].multiply(-1)

        layout = go.Layout(
            barmode="relative",
            title="Aggregated Supply and demand for <br> {} scenario".format(scenario),
            width=400,
            yaxis=dict(
                title="Energy in TWh",
                titlefont=dict(size=16, color="rgb(107, 107, 107)"),
                tickfont=dict(size=14, color="rgb(107, 107, 107)"),
            ),
        )

        data = [
            go.Bar(
                x=row.index,
                y=row.values,
                text=[v.round(1) for v in row.values],
                textposition="auto",
                name=idx,
                marker=dict(color=app.color_dict.get(idx.lower(), "gray")),
            )
            for idx, row in agg.to_frame().T.iteritems()
        ]

        return {"data": data, "layout": layout}
