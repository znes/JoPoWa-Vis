import os

from pkg_resources import resource_filename
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import toml

from oemof.tabular.tools.plots import color_dict


# external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.css.append_css({"external_url": "/static/{}".format("bWLwgP.css")})

app.config.suppress_callback_exceptions = True

config = toml.load(resource_filename("jopowa_vis", "config.toml"))

# update color dictionary for plots
color_dict.update(config["colors"])
app.color_dict = color_dict

# mapper for mapping technologies to profile names
app.profile_mapper = config["profile_mapper"]

# read basic data

app.profiles = pd.read_csv(
    resource_filename("jopowa_vis", config["paths"]["profiles"]),
    index_col=0,
    parse_dates=True,
)

results_directory = os.path.join(os.path.expanduser("~"), "jopowa-vis", "results")

if not os.path.exists(results_directory):
    os.makedirs(results_directory)


if set(app.profiles) != set(app.profile_mapper.values()):
    raise ValueError("Missing key/values in profile mapper.")
