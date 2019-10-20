import os

import pandas as pd
import plotly.graph_objs as go

from jopowa_vis import app


def hourly_power_plot(df, scenario, config):
    """
    """

    data = []

    layout = go.Layout(
        barmode="stack",
        title="Hourly supply and demand in for <br> scenario {}.".format(scenario),
        yaxis=dict(
            title="Supply and Demand in {}".format(config["units"]["power"]),
            titlefont=dict(size=16, color="rgb(107, 107, 107)"),
            tickfont=dict(size=14, color="rgb(107, 107, 107)"),
        ),
    )

    for c in df.columns:
        if "demand" in c:
            data.append(
                go.Scatter(
                    x=df.index,
                    y=df[c],
                    name=c,
                    line=dict(width=3, color=app.color_dict.get(c.lower(), "black")),
                )
            )
        elif c == "excess":
            data.append(
                go.Scatter(
                    x=df.index,
                    y=df[c] * -1,
                    name=c,
                    stackgroup="negative",
                    line=dict(width=0, color=app.color_dict.get(c.lower(), "black")),
                )
            )
        elif "storage" in c:
            data.append(
                go.Scatter(
                    x=df.index,
                    y=df[c].clip(lower=0),
                    name=c,
                    stackgroup="positive",
                    line=dict(width=0, color=app.color_dict.get(c.lower(), "black")),
                    showlegend=True,
                )
            )
            data.append(
                go.Scatter(
                    x=df.index,
                    y=df[c].clip(upper=0),
                    name=c,
                    stackgroup="negative",
                    line=dict(width=0, color=app.color_dict.get(c.lower(), "black")),
                    showlegend=False,
                )
            )
        else:
            data.append(
                go.Scatter(
                    x=df.index,
                    fillcolor=app.color_dict.get(c.lower(), "black"),
                    y=df[c].clip(lower=0),
                    name=c,
                    stackgroup="positive",
                    line=dict(width=0, color=app.color_dict.get(c.lower(), "black")),
                )
            )
    return {"data": data, "layout": layout}


def aggregated_supply_demand(results_directory, scenarios, config):
    """
    """
    agg_df = pd.DataFrame()
    for s in scenarios:
        if os.path.exists(os.path.join(results_directory, s + ".csv")):
            df = pd.read_csv(
                os.path.join(results_directory, s + ".csv"),
                parse_dates=True,
                index_col=0,
            )
            agg = df[df > 0].sum() / 1e3  # -> TWh
            agg[["demand", "excess"]] = agg[["demand", "excess"]].multiply(-1)
            agg["storage-consumption"] = (
                df["storage"].clip(upper=0).sum() / 1e3
            )  # -> TWh
            agg_df = pd.concat([agg_df, agg], axis=1)
    agg_df.columns = scenarios
    agg_df = agg_df.T
    agg_df = agg_df.reindex(sorted(agg_df.index), axis=0)

    layout = go.Layout(
        barmode="relative",
        title="Aggregated supply and demand",
        width=400,
        yaxis=dict(
            title="Energy in {}".format(config["units"]["energy"]),
            titlefont=dict(size=16, color="rgb(107, 107, 107)"),
            tickfont=dict(size=14, color="rgb(107, 107, 107)"),
        ),
    )

    mapper = {"storage-consumption": "storage"}
    data = []
    for idx, row in agg_df.iteritems():
        if idx == "storage-consumption":
            legend = False
        else:
            legend = True
        data.append(
            go.Bar(
                x=row.index,
                y=row.values,
                text=[v.round(2) for v in row.values],
                hovertext=[
                    ", ".join([str(v.round(2)), mapper.get(idx, idx)])
                    for v in row.values
                ],
                hoverinfo="text",
                textposition="auto",
                showlegend=legend,
                name=mapper.get(idx, idx),
                marker=dict(
                    color=app.color_dict.get(mapper.get(idx, idx).lower(), "gray")
                ),
            )
        )

    return {"data": data, "layout": layout}


def empty_plot(label_annotation):
    """
    Returns an empty plot with a centered text.
    """

    trace1 = go.Scatter(x=[], y=[])

    data = [trace1]

    layout = go.Layout(
        showlegend=False,
        xaxis=dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks="",
            showticklabels=False,
        ),
        yaxis=dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks="",
            showticklabels=False,
        ),
        annotations=[
            dict(
                x=0,
                y=0,
                xref="x",
                yref="y",
                text=label_annotation,
                showarrow=False,
                arrowhead=0,
                ax=0,
                ay=0,
            )
        ],
    )

    return {"data": data, "layout": layout}


def stacked_capacity_plot(df, config):
    return {
        "data": [
            go.Bar(
                name=idx,
                x=row.index,
                y=row.values,
                marker=dict(color=app.color_dict.get(idx.lower(), "black")),
            )
            for idx, row in df.iterrows()
            if idx not in ["Demand", "Storage Capacity"]
        ]
        + [
            go.Scatter(
                mode="markers",
                name="Demand (el)",
                x=df.columns,
                y=df.loc["Demand"].values,
                marker=dict(
                    color=app.color_dict.get("demand", "darkblue"),
                    size=12,
                    line=dict(color="DarkSlateGray", width=2),
                ),
                yaxis="y2",
            )
        ],
        "layout": go.Layout(
            barmode="stack",
            title="Installed capacities and demand",
            legend=dict(x=1.1, y=0),
            yaxis=dict(
                title="Capacity in {}".format(config["units"]["power"]),
                titlefont=dict(size=16, color="rgb(107, 107, 107)"),
                tickfont=dict(size=14, color="rgb(107, 107, 107)"),
            ),
            yaxis2=dict(
                title="Demand in {}".format(config["units"]["energy"]),
                overlaying="y",
                rangemode="tozero",
                autorange=True,
                side="right",
                showgrid=False,
            ),
        ),
    }
