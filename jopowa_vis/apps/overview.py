import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table

import multiprocessing as mp
import pandas as pd
import plotly.graph_objs as go

from jopowa_vis.app import app, results_directory, config
from jopowa_vis.apps import calculations, optimization

import io
import base64

upload = html.Div(
    [
        dcc.Upload(
            id="datatable-upload",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
        )
    ]
)


def parse_contents(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    if "csv" in filename:
        # Assume that the user uploaded a CSV file
        return pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    elif "xls" in filename:
        # Assume that the user uploaded an excel file
        return pd.read_excel(io.BytesIO(decoded))


@app.callback(
    [
        Output("scenario-table-technology", "data"),
        Output("scenario-table-technology", "columns"),
    ],
    [
        Input("add-column-button", "n_clicks"),
        Input("datatable-upload", "contents"),
    ],
    [
        State("datatable-upload", "filename"),
        State("add-column-input", "value"),
        State("scenario-table-technology", "data"),
        State("scenario-table-technology", "columns"),
    ],
)
def update_output(
    n_clicks, contents, filename, value, existing_data, existing_columns
):
    # need to return a valid column is callback is called
    if existing_columns is None:
        return [{}], [{"id": "Technology", "name": "Technology"}]

    # if callback is triggered by button
    if n_clicks > 0:
        existing_columns.append(
            {
                "id": value,
                "name": value,
                "renamable": False,
                "deletable": True,
                "type": "numeric",
            }
        )
        return existing_data, existing_columns

    if contents is None:
        return existing_data, existing_columns

    df = parse_contents(contents, filename)
    return (
        df.to_dict("records"),
        [
            {"id": col, "name": col, "renamable": False, "deletable": True}
            for col in df.columns
        ],
    )


table = dbc.Card(
    [
        dbc.CardHeader([]),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            children=[
                                dash_table.DataTable(
                                    id="scenario-table-technology",
                                    data=[{}],
                                    editable=True,
                                )
                            ],
                            width=6,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Input(
                                    id="add-column-input",
                                    type="text",
                                    value="",
                                    placeholder="Please enter scenario name...",
                                ),
                                dbc.Button(
                                    "Add scenario",
                                    id="add-column-button",
                                    n_clicks=0,
                                    color="secondary",
                                ),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Button(
                                    "Save Changes",
                                    id="save-button",
                                    n_clicks=0,
                                    color="primary",
                                ),
                                html.Div(id="save-output"),
                            ],
                            width={"order": "last"},
                        ),
                    ],
                    justify="between",
                ),
            ]
        ),
    ]
)

# Scenario Plots ---------------------
plots = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [dcc.Graph(id="scenario-residual-load-plot")],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dcc.Graph(
                                    id="scnenario-table-values-output",
                                    figure={
                                        "layout": go.Layout(
                                            barmode="stack",
                                            title="Installed capacities",
                                        )
                                    },
                                )
                            ],
                            width=6,
                        ),
                    ],
                    form=True,
                )
            ]
        )
    ],
    className="mt-3",
)


layout = html.Div([upload, table, plots])


# save scenario changes -------------------------------------------------------
@app.callback(
    Output("save-output", "children"),
    [Input("save-button", "n_clicks")],
    state=[State("scenario-table-technology", "data")],
)
def save_scenario_changes(n_clicks, data):
    if n_clicks > 0:
        df = pd.DataFrame(data).set_index("Technology")

        sc = os.path.join(results_directory, "capacity.csv")
        # if os.path.isfile(sc):
        #     return False, True
        # else:
        df.to_csv(sc)

        return "Saved and computed"
    else:
        return ""


# stacked capacity plot -------------------------------------------------------
@app.callback(
    Output("scnenario-table-values-output", "figure"),
    [
        Input("scenario-table-technology", "data"),
        Input("scenario-table-technology", "columns"),
    ],
)
def display_output(data, columns):
    df = pd.DataFrame(data)
    # check if dataframe is empty to avoid errors
    if df.empty:
        return {}

    df = pd.DataFrame(data).set_index("Technology")

    return {
        "data": [
            go.Bar(
                name=idx,
                x=row.index,
                y=row.values,
                marker=dict(color=app.color_dict.get(idx.lower(), "black")),
            )
            for idx, row in df.iterrows()
            if idx not in ["Demand", "Storage Capacity"]
        ]
        + [
            go.Scatter(
                mode="markers",
                name="Demand (el)",
                x=df.columns,
                y=df.loc["Demand"].values,
                marker=dict(
                    color="Pink",
                    size=12,
                    line=dict(color="DarkSlateGrey", width=2),
                ),
                yaxis="y2",
            )
        ],
        "layout": go.Layout(
            barmode="stack",
            title="Installed capacities and demand scenarios",
            legend=dict(x=1.1, y=0),
            yaxis=dict(
                title="Capacity in {}".format(config["units"]["power"]),
                titlefont=dict(size=16, color="rgb(107, 107, 107)"),
                tickfont=dict(size=14, color="rgb(107, 107, 107)"),
            ),
            yaxis2=dict(
                title="Demand in TWh",
                overlaying="y",
                rangemode="tozero",
                autorange=True,
                side="right",
                showgrid=False,
            ),
        ),
    }


# residual load plot ----------------------------------------------------------
@app.callback(
    Output("scenario-residual-load-plot", "figure"),
    [
        Input("scenario-table-technology", "data"),
        Input("scenario-table-technology", "columns"),
    ],
)
def display_timeseries(data, scenarios):
    df = pd.DataFrame(data)

    # check if dataframe is empty to avoid errors
    if df.empty:
        return {}
    # fill nas to avoid errors in plots (e.g. when converting )
    df = df.fillna(0)
    df.set_index("Technology", inplace=True)

    # convert to float
    for c in df.columns:
        df[c] = df[c].astype("float")

    # if not df.isnull().values.any():
    residual_load = {}
    for c in df.columns:
        residual_load[c] = (
            calculations.timeseries(df[c])["RL"]
            .sort_values(ascending=False)
            .values
        )

    return {
        "data": [
            go.Scatter(name=k, x=[i for i in range(8760)], y=v)
            for k, v in residual_load.items()
        ],
        "layout": go.Layout(
            title="Sorted residual load for scenarios (duration curve)",
            legend=dict(x=1.1, y=0),
            yaxis=dict(
                title="Energy in {}".format(config["units"]["energy"]),
                titlefont=dict(size=16, color="rgb(107, 107, 107)"),
                tickfont=dict(size=14, color="rgb(107, 107, 107)"),
            ),
        ),
    }
