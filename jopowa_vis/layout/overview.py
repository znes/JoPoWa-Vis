import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
from dash_table.Format import Format

import multiprocessing as mp
import pandas as pd
import plotly.graph_objs as go

from jopowa_vis.app import app, results_directory, config
from jopowa_vis.apps import calculations, plots, optimization

import io
import base64

upload = dbc.Row(
    [
        dbc.Col(
            [
                dcc.Upload(
                    id="datatable-upload",
                    children=html.Div(
                        ["Drag and Drop or ", html.A("Scenario File")]
                    ),
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
            ],
            width={"size": 8, "offset": 2},
        )
    ],
    justify="between",
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


table = dbc.Card(
    [
        dbc.CardHeader([]),
        dbc.CardBody(
            [                           dbc.Alert("", id="alert", dismissable=True, is_open=False),

                dbc.Row(
                    [
                        dbc.Col(
                            children=[
                                dash_table.DataTable(
                                    id="scenario-table-technology",
                                    style_as_list_view=True,
                                    style_cell={
                                        "padding": "5px",
                                        "height": "auto",
                                        "minWidth": "0px",
                                        "maxWidth": "120px",
                                        "whiteSpace": "normal",
                                    },
                                    style_header={
                                        "backgroundColor": "white",
                                        "fontWeight": "bold",
                                    },
                                    style_cell_conditional=[
                                        {
                                            "if": {"column_id": c},
                                            "textAlign": "left",
                                        }
                                        for c in ["Technology"]
                                    ],
                                    data=[{}],
                                    editable=True,
                                )
                            ],
                            width="auto",
                        ),
                        dbc.Col(
                            [dcc.Graph(id="scnenario-table-values-output")]
                        ),
                    ],
                    justify="between",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Input(
                                    id="add-column-input",
                                    type="text",
                                    value="",
                                    placeholder="Please enter column name...",
                                ),
                                dbc.Button(
                                    "Add scenario",
                                    id="add-column-button",
                                    n_clicks=0,
                                    color="secondary",
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Input(
                                    id="save-scenario-input",
                                    type="text",
                                    value="",
                                    placeholder="Enter scenario set name...",
                                ),
                                dbc.Button(
                                    "Save Changes",
                                    id="save-button",
                                    n_clicks=0,
                                    color="primary",
                                ),
                            ],
                            width={"order": "last", "size": 3},
                        ),
                    ],
                    justify="between",
                ),
            ]
        ),
    ]
)


plot_card = dbc.Card(
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
                                # dcc.Graph(
                                #     id="scnenario-table-values-output",
                                # )
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


layout = html.Div([upload, table, plot_card])

##############################################################################
# CALLBACKS
##############################################################################


# update table ----------------------------------------------------------------
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
            {"id": col, "name": col, "renamable": False, "deletable": True,
             "format": Format(nully=0)}
            for col in df.columns
        ],
    )


# save scenario changes -------------------------------------------------------
@app.callback(
    [Output("alert", "children"),
    Output("alert", "is_open"),
    Output("alert", "color"),
    Output("update-dirlist", "n_clicks")],
    [Input("save-button", "n_clicks"), Input("save-scenario-input", "value")],
    state=[State("scenario-table-technology", "data")],
)
def save_scenario_changes(n_clicks, scenario_set_name, data):
    if n_clicks > 0:
        df = pd.DataFrame(data).set_index("Technology")

        dir = os.path.join(results_directory, scenario_set_name)
        if not os.path.exists(dir):
            os.makedirs(dir)

        df.to_csv(os.path.join(dir, "capacity.csv"))
        p = mp.Pool(5)
        check = p.starmap(optimization.compute, [(i, dir) for i in df.columns.values])
        if False in check:
            return "An error occured during optimization!", True, "danger", 0
        else:
            return "Saved. Computation successful!", True, "success", 1
    else:
        return "", False, "", 0


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
        return plots.empty_plot("")

    df = pd.DataFrame(data).set_index("Technology")

    plot = plots.stacked_capacity_plot(df, config)
    plot["layout"].update({"width": 600})
    return plot


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
        return plots.empty_plot("")
    # fill nas to avoid errors in plots (e.g. when converting )
    df = df.fillna(0)
    df.set_index("Technology", inplace=True)

    # convert to float
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

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
