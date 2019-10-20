import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from jopowa_vis.app import app, config, results_directory
from jopowa_vis.layout import (
    start_page,
    overview,
    power_system,
    results_overview,
)


app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

index_page = dbc.Card(
    [
        dbc.CardHeader(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2(
                                    config["headings"]["title"],
                                    className="card-title",
                                ),
                                html.H3(config["headings"]["sub-title"]),
                            ]
                        ),
                        dbc.Col(
                            [
                                html.Img(
                                    src="https://www.uni-flensburg.de/"
                                    "fileadmin/content/portale/oeffentliches/"
                                    "dokumente/infomaterial/logos/"
                                    "logo-universitaet/druck/"
                                    "europa-universitaet-flensburg-hauptlogo"
                                    "-cmyk-300dpi.png",
                                    height="50dpi",
                                ),
                                html.Img(
                                    src="https://energydata.info/"
                                    "uploads/group/"
                                    "2016-12-08-160800.244704giz-logo.png",
                                    height="50dpi",
                                    style={"align": "right"},
                                ),
                            ],
                            width={"order": "last", "size": 3},
                        ),
                    ]
                )
            ]
        ),
        dbc.CardBody(
            [
                # select menu
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                # could be filled ...
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.Button(
                                    "Update Results",
                                    id="update-dirlist",
                                    n_clicks=0,
                                    color="secondary",
                                )
                            ],
                            width={"order": "last", "offset": 0},
                            align="center",
                        ),
                    ]
                ),
                dbc.Tabs(
                    [
                        dbc.Tab(start_page.map, label="Start Page"),
                        dbc.Tab(overview.layout, label="Scenario Overview"),
                        dbc.Tab(
                            results_overview.layout, label="Results Overview"
                        ),
                        dbc.Tab(power_system.layout, label="Scenario Results"),
                    ]
                ),
            ]
        ),
        dbc.CardFooter([]),
    ]
)


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/overview":
        return overview.layout
    else:
        return index_page


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


@app.callback(
    Output("scenario-select-id", "options"),
    [Input("directory-select-id", "value")],
)
def update_scenario_select(scenario_set):
    if scenario_set is None:
        return []
    files = os.listdir(os.path.join(results_directory, scenario_set))
    scenarios = [
        s.replace(".csv", "")
        for s in files
        if s.endswith(".csv") and s != "capacity.csv"
    ]
    return [{"label": f, "value": f} for f in scenarios]


def serve():
    app.run_server(debug=True)


if __name__ == "__main__":
    app.run_server(debug=True)
