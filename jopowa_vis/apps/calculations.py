import pandas as pd

from jopowa_vis.app import app


def timeseries(data):
    """ Calculates absolute timeseries based on scenario table entries and
    normed profiles

    Parameters
    ----------
    data : pd.Series
        Series with scenario information on installed capacities and
        energy (e.g. Demand.). Indices are supply technologies / demand.
        Tame of series is the scenario.
    """
    ts = pd.DataFrame.from_dict(
        {
            tech: value * app.profiles[app.profile_mapper[tech]]
            for tech, value in data.iteritems()
            if tech in app.profile_mapper.keys()
        }
    ).set_index(app.profiles.index)
    ts["Demand"] = ts["Demand"] * 1e3  # -> TWh
    ts["RL"] = ts["Demand"] - ts[["Wind", "PV", "CSP"]].sum(axis=1)
    ts["Other"] = ts["RL"][ts["RL"] > 0]
    ts["Excess"] = ts["RL"][ts["RL"] < 0] * -1

    ts.fillna(0, inplace=True)

    return ts
