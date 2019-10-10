import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# import dash_table

import pandas as pd
import plotly.graph_objs as go

from jopowa_vis.app import app

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
                                dcc.Graph(
                                    id="hourly-production-graph", figure={}
                                )
                            ],
                            width=8,
                        ),
                        dbc.Col(
                            [
                                dcc.Graph(
                                    id="supply_demand_aggr_graph", figure={}
                                )
                            ],
                            width=4,
                        ),
                    ]
                )
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
)
def display_hourly_graph(rows, scenario):
    if scenario == "" or scenario is None:
        return {}
    else:
        df = pd.DataFrame(rows).set_index("Technology")

        layout = go.Layout(
            barmode="stack",
            title="Hourly supply and demand in for <br> scenario {}.".format(
                scenario
            ),
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

        for c, val in df[scenario].iteritems():
            if c in app.profile_mapper.keys():
                if "Demand" in c:
                    data.append(
                        go.Scatter(
                            x=app.profiles.index,
                            y=float(val)
                            * 1000
                            * app.profiles[app.profile_mapper.get(c)],
                            name=c,
                            line=dict(width=3, color="darkred"),
                        )
                    )
                else:
                    data.append(
                        go.Scatter(
                            x=app.profiles.index,
                            fillcolor=app.color_dict.get(c.lower(), "black"),
                            y=float(val)
                            * app.profiles[app.profile_mapper.get(c)],
                            name=c,
                            stackgroup="positive",
                            line=dict(
                                width=0,
                                color=app.color_dict.get(c.lower(), "black"),
                            ),
                        )
                    )
        return {"data": data, "layout": layout}


@app.callback(
    Output("supply_demand_aggr_graph", "figure"),
    [
        Input("scenario-table-technology", "data"),
        Input("scenario-select-id", "value"),
    ],
)
def display_aggregated_supply_demand_graph(rows, scenario):
    if scenario == "" or scenario is None:
        return {}
    else:
        df = pd.DataFrame(rows).set_index("Technology")

        aggregated_supply = {}
        for tech, value in df[scenario].iteritems():
            if tech in ["Wind", "PV", "CSP"]:
                aggregated_supply[tech] = (
                    value * app.profiles[app.profile_mapper[tech]]
                ).sum() / 1000  # MWh ->GWh

        # other production is defined as demand - all renewlabes collected above
        # no multiplication necessary, as Demand is in GWh
        aggregated_supply["other"] = df.at["Demand", scenario] - sum(
            [p for p in aggregated_supply.values()]
        )
        if aggregated_supply["other"] < 0:
            aggregated_supply["other"] = 0

        aggr_df = pd.Series(aggregated_supply).to_frame()

        layout = go.Layout(
            barmode="stack",
            title="Aggregated Supply and demand for <br> {} scenario".format(
                scenario
            ),
            width=400,
            yaxis=dict(
                title="Energy in GWh",
                titlefont=dict(size=16, color="rgb(107, 107, 107)"),
                tickfont=dict(size=14, color="rgb(107, 107, 107)"),
            ),
        )

        data = [
            go.Bar(
                x=row.index,
                y=row.values,
                name=idx,
                marker=dict(color=app.color_dict.get(idx.lower(), "gray")),
            )
            for idx, row in aggr_df.T.iteritems()
        ]

        return {"data": data, "layout": layout}
