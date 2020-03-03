# -*- coding: utf-8 -*-

"""Top-level package for JoPoWa-Vis."""

__author__ = """Simon Hilpert"""
__email__ = "simon.hilpert@uni-flensburg.de"
__version__ = "0.0.1"


from flask import Flask
import dash

import os

from pkg_resources import resource_filename
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import toml

from oemof.tabular.tools.plots import color_dict

def create_app():

    # Adapted from https://github.com/okomarov/dash_on_flask/blob/76ffc3cb792c067d0112919ec58f38fe37e2c4a7/app/dashapp.py
    app = Flask(__name__)
    external_stylesheets = ["/static/{}".format("bWLwgP.css")]
    dashapp = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/', external_stylesheets=[dbc.themes.BOOTSTRAP])

    from jopowa_vis.dashapp import app_bp
    app.register_blueprint(app_bp)

    # dashapp.css.dashappend_css({"external_url": "/static/{}".format("bWLwgP.css")})

    dashapp.config.suppress_callback_exceptions = True

    config = toml.load(resource_filename("jopowa_vis", "config.toml"))

    # update color dictionary for plots
    color_dict.update(config["colors"])
    dashapp.color_dict = color_dict

    # mdashapper for mdashapping technologies to profile names
    # dashapp.profile_mdashapper = config["profile_mdashapper"]

    # read basic data

    dashapp.profiles = pd.read_csv(
        resource_filename("jopowa_vis", config["paths"]["profiles"]),
        index_col=0,
        parse_dates=True,
    )

    results_directory = os.path.join(
        os.path.expanduser("~"), "jopowa-vis", "results"
    )

    if not os.path.exists(results_directory):
        os.makedirs(results_directory)


    # if set(dashapp.profiles) != set(dashapp.profile_mdashapper.values()):
        #raise ValueError("Missing key/values in profile mdashapper.")

    return app, dashapp
