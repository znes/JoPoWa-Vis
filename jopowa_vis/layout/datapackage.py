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
from datapackage import Package

from jopowa_vis.app import app, results_directory, config
from jopowa_vis.apps import calculations, plots, optimization


form = dbc.Row(
    [
        dbc.Col(
            [
            dbc.FormGroup(
                [
                    dbc.Label("Upload datapackage"),
                dbc.Input(
                    id="datapackage-input",
                    type="text",
                    value="",
                    placeholder="Please insert link...",
                ),
                dbc.Button(
                    "Add datapackage",
                    id="add-datapackage-button",
                    n_clicks=0,
                    color="secondary",
                ),
            ]
        )],
            width=3
        ),
        dbc.Col(
            [
                dbc.FormGroup(
                    [
                        dbc.Label("Select Resource"),
                        dcc.Dropdown(
                            id="datapackage-resources",
                            className="mb-3",
                        ),
                    ]
                )
            ],
            width={"size": 2, "order": "last"},
        ),
    ]  # ,  justify="between"
)

resource_table = dbc.Card(
        [
        dbc.CardHeader(id="resource-header", children=["Resource Table"]),
        dbc.CardBody(
            [
                dash_table.DataTable(
                    id="resource-table",
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
                    columns=[{"name": "name", "id": "name"}],
                    style_cell_conditional=[
                        {
                            "if": {"column_id": c},
                            "textAlign": "left",
                        }
                        for c in ["name"]
                    ],
                    data=[{}],
                    editable=True,
                    dropdown={}
                ),
                html.Div(id='table-dropdown-container')
            ]
        ),
    ]
)

#tables = html.Div(id="tables-id", children=[])


layout = [form, resource_table]


@app.callback(
    [Output("tables-id", "children"),
     Output("datapackage-resources", "options")],
    [Input("add-datapackage-button", "n_clicks"),
     Input("datapackage-input", "value")],
)
def add_datapackage(n_clicks, datapackage):
    if n_clicks > 0:
        dpkg = Package(datapackage)
        dataframes = {}

        for res in dpkg.resources:
            if res is not None and "data/elements" in res.descriptor["path"]:
                dataframes[res.name] = pd.DataFrame.from_dict(
                    res.read(keyed=True)).astype(str)

        return [None], [{"label": r.name, "value": r.name} for r in dpkg.resources]
    else:
        return [], []

    #     return [[
    #         dbc.Card(
    #             [
    #                 dbc.CardHeader([n]),
    #                 dbc.CardBody(
    #                     [
    #                         dash_table.DataTable(
    #                             id="scenario-table-technology-" + n,
    #                             style_as_list_view=True,
    #                             style_cell={
    #                                 "padding": "5px",
    #                                 "height": "auto",
    #                                 "minWidth": "0px",
    #                                 "maxWidth": "120px",
    #                                 "whiteSpace": "normal",
    #                             },
    #                             style_header={
    #                                 "backgroundColor": "white",
    #                                 "fontWeight": "bold",
    #                             },
    #                             columns=[{"name": i, "id": i} for i in df.columns],
    #                             # style_cell_conditional=[
    #                             #     {
    #                             #         "if": {"column_id": c},
    #                             #         "textAlign": "left",
    #                             #     }
    #                             #     for c in ["Technology"]
    #                             # ],
    #                             data=df.to_dict("rows"),
    #                             editable=True,
    #                         )
    #                     ]
    #                 ),
    #             ]
    #         )
    #         for n, df in dataframes.items()
    #     ]]
    # else:
    #     return [None]


@app.callback(
    [Output("resource-header", "children"),
     Output("resource-table", "columns"),
     Output("resource-table", "data"),
     Output("resource-table", "dropdown")],
    [Input("datapackage-resources", "value")],
    state=[State("datapackage-input", "value")]
)
def show_resource_table(resource, datapackage):

    dpkg = Package(datapackage)
    res = dpkg.get_resource(resource)

    if res is not None:
        df = pd.DataFrame.from_dict(res.read(keyed=True)).astype(str)

        #df.set_index("name", inplace=True)
        df.sort_index(axis=1, inplace=True)
        columns = [
            {
                "id": col,
                "name": col,
                "renamable": False,
                "deletable": True,
                "format": Format(nully=0),
            }
            for col in df.columns
        ]

        dropdown = {
            'profile': {
                'options': [
                    {'label': i["name"], 'value': i["name"]}
                    for i in dpkg.get_resource("generator-profiles").descriptor["schema"]["fields"]
                    if i["name"] != "timeindex"


                ]
            }
        }
        import pdb;pdb.set_trace()

        return (
            [resource.title()],
            columns,
            df.to_dict("records"),
            dropdown
        )
    else:

        return ["Resource Template"], [{"id": "name", "name": "name"}], [{}], {}
