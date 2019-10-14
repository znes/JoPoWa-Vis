import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table

import pandas as pd
import plotly.graph_objs as go

from jopowa_vis.app import app
from jopowa_vis.apps import calculations

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
            {"id": value, "name": value, "renamable": False, "deletable": True}
            for value in df.columns
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
                                ),
                                dbc.FormGroup(
                                    [
                                        dbc.Label("Add scenario"),
                                        dbc.Input(
                                            id="add-column-input",
                                            type="text",
                                            value="",
                                        ),
                                        dbc.FormText(
                                            "Please enter scenario name..."
                                        ),
                                        dbc.Button(
                                            "Add column",
                                            id="add-column-button",
                                            n_clicks=0,
                                        ),
                                    ]
                                ),
                            ],
                            width=6,
                        )
                    ]
                )
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

safe_scenarios = dbc.Row(
    [
        dbc.FormGroup(
            id="form",
            children=[
                dbc.Label("Save Scenarios"),
                dbc.Input(id="new-scenarios", type="text", value=""),
                dbc.FormText("Enter new scenario set name..."),
                dbc.FormFeedback("Scenario set saved!", valid=True),
                dbc.FormFeedback("Scenario set name exists!", valid=False),
                dbc.Button("Save Changes", id="button"),
            ],
        )
    ]
)

layout = html.Div([upload, table, plots, safe_scenarios])


# save scenario changes -------------------------------------------------------
@app.callback(
    [Output("new-scenarios", "valid"), Output("new-scenarios", "invalid")],
    [Input("button", "n_clicks")],
    state=[
        State("new-scenarios", "value"),
        State("scenario-table-technology", "data"),
    ],
)
def save_scenario_changes(n_clicks, scenario_name, data):
    df = pd.DataFrame(data).set_index("Technology")

    directory = os.path.join(
        os.path.expanduser("~"), "jopowa-vis", "scenarios"
    )

    if not os.path.exists(directory):
        os.makedirs(directory)

    sc = os.path.join(directory, scenario_name + ".csv")
    if os.path.isfile(sc):
        return False, True
    else:
        df.to_csv(sc)
        return True, False


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
            if idx != "Demand"
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
                title="Capacity in MW",
                titlefont=dict(size=16, color="rgb(107, 107, 107)"),
                tickfont=dict(size=14, color="rgb(107, 107, 107)"),
            ),
            yaxis2=dict(
                title="Demand in MWh",
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
        ]
    }
