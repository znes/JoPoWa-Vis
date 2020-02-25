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


form = dbc.Row(
    [
        dbc.Col(
            [
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
            ],
            width=3,
        ),
    ]  # ,  justify="between"
)

tables = html.Div(id="tables-id", children=[])


layout = [tables, form]

from datapackage import Package
@app.callback(
    [Output("tables-id", "children")],
    [Input("add-datapackage-button", "n_clicks"),
     Input("datapackage-input", "value")],
)
def add_datapackage(n_clicks, datapackage):
    if n_clicks > 0:

        dpkg = Package(datapackage)
        dataframes = {}

        #path = "/home/admin/datapackages/dispatch/data/elements"
        #dirs = os.listdir(path)
        #import pdb; pdb.set_trace()
        for res in dpkg.resources:
            if res is not None and "data/elements" in res.descriptor["path"]:
                dataframes[res.name] = pd.DataFrame.from_dict(
                    res.read(keyed=True))
                    
        # dataframes = {}
        # for d in dirs:
        #     dataframes[d.replace(".csv", "").title()] = pd.read_csv(
        #         os.path.join(path, d), sep=";"
        #     ).round(3)

        return [[
            dbc.Card(
                [
                    dbc.CardHeader([n]),
                    dbc.CardBody(
                        [
                            dash_table.DataTable(
                                id="scenario-table-technology-" + n,
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
                                columns=[{"name": i, "id": i} for i in df.columns],
                                # style_cell_conditional=[
                                #     {
                                #         "if": {"column_id": c},
                                #         "textAlign": "left",
                                #     }
                                #     for c in ["Technology"]
                                # ],
                                data=df.to_dict("rows"),
                                editable=True,
                            )
                        ]
                    ),
                ]
            )
            for n, df in dataframes.items()
        ]]
    else:
        return [None]
