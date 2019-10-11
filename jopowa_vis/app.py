from pkg_resources import resource_filename
import dash
import dash_bootstrap_components as dbc

import pandas as pd
import toml

from oemof.tabular.tools.plots import color_dict

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.config.suppress_callback_exceptions = True

config = toml.load(resource_filename("jopowa_vis", "config.toml"))

# update color dictionary for plots
color_dict.update(config["colors"])
app.color_dict = color_dict

# mapper for mapping technologies to profile names
app.profile_mapper = config["profile_mapper"]

# read basic data
start_scenarios = pd.read_csv(
    resource_filename("jopowa_vis", config["paths"]["start-scenarios"]),
    index_col=0,
)
app.profiles = pd.read_csv(
    resource_filename("jopowa_vis", config["paths"]["profiles"]),
    index_col=0,
    parse_dates=True,
)

if set(app.profiles) != set(app.profile_mapper.values()):
    raise ValueError("Missing key/values in profile mapper.")
