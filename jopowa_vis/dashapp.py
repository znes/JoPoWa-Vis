
# Copied from https://github.com/okomarov/dash_on_flask/blob/76ffc3cb792c067d0112919ec58f38fe37e2c4a7/app/dashapp.py
from flask import Blueprint


app_bp = Blueprint('main', __name__)


@app_bp.route('/')
def index():
    return "Hello"
