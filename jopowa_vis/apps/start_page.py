import dash_bootstrap_components as dbc
import dash_core_components as dcc

import plotly.graph_objs as go


map = dbc.Col([
        dcc.Graph(
            id='jordan-map',
            figure={
                "data": [go.Scattermapbox(
                    lat=['31.963158'],
                    lon=['35.930359'],
                    mode='markers',
                    marker=go.scattermapbox.Marker(
                        size=14
                    ),
                    text=['Amman'],
                )],
                "layout": go.Layout(
                    title = '',
                    height = 500,
                    margin=dict(l=20, r=20, t=20, b=20),
                    mapbox_style="open-street-map",
                    mapbox=go.layout.Mapbox(
                         bearing=0,
                         center=go.layout.mapbox.Center(
                            lat=31,
                            lon=35),
                         pitch=0,
                         zoom=5.5,
                         style='light'
                    )
                )
            }
        )
        ], width=6)
