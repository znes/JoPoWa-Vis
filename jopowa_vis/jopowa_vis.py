import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from jopowa_vis.app import app, config
from jopowa_vis.apps import start_page, overview, power_system


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
                                    config["headings"]["title"], className="card-title"
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
                                dbc.FormGroup(
                                    [
                                        dbc.Label("Select scenario"),
                                        dcc.Dropdown(
                                            id="scenario-select-id", className="mb-3"
                                        ),
                                    ]
                                )
                            ],
                            width={"size": 2, "order": "last"},
                        ),
                    ]
                ),
                dbc.Tabs(
                    [
                        dbc.Tab(start_page.map, label="Start Page"),
                        dbc.Tab(overview.layout, label="Scenario Overview"),
                        dbc.Tab(power_system.layout, label="Power System")
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
    Output("scenario-select-id", "options"),
    [Input("scenario-table-technology", "columns")],
)
def update_scenario_select(columns):
    if columns is None:
        return None

    return [
        {"label": c["id"], "value": c["name"]}
        for c in columns
        if c["id"] != "Technology"
    ]


def serve():
    app.run_server(debug=True)


if __name__ == "__main__":
    app.run_server(debug=True)
