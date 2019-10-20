# -*- coding: utf-8 -*-
import os

from datapackage import Package
import pandas as pd
from pyomo.environ import ConcreteModel, Var, Constraint, Objective, Expression
from pyomo.environ import NonNegativeReals, Reals, minimize
from pyomo.opt import SolverFactory

from jopowa_vis.app import results_directory


def compute(
    scenario,
    scenario_set_path=results_directory,
    input_datapath="jopowa_vis/data/jordan-input-data",
    renewables=["wind", "pv", "csp", "hydro"],
    initial_storage_level=0.5,
):
    """
    """
    data = pd.read_csv(os.path.join(scenario_set_path, "capacity.csv")).set_index(
        "Technology"
    )
    if scenario not in data.columns:
        return False

    data = data[scenario]
    data.index = [i.lower() for i in data.index]

    profiles = pd.read_csv(
        os.path.join(input_datapath, "profile/energy-water-profile.csv"),
        sep=",",
        parse_dates=True,
        index_col=0,
    )

    technology = pd.DataFrame(
        Package(os.path.join(input_datapath, "technology/datapackage.json"))
        .get_resource("technology")
        .read(keyed=True)
    ).set_index(["parameter", "carrier"])

    carrier_cost = pd.DataFrame(
        Package(os.path.join(input_datapath, "carrier/datapackage.json"))
        .get_resource("carrier-cost")
        .read(keyed=True)
    ).set_index(["scenario", "carrier"])

    emission_factor = pd.DataFrame(
        Package(os.path.join(input_datapath, "carrier/datapackage.json"))
        .get_resource("emission-factor")
        .read(keyed=True)
    ).set_index(["carrier"])

    timesteps = profiles.index[:]

    demand = (profiles["demand"] * data["demand"]) * 1e3  # -> TWh

    volatile = pd.DataFrame(
        {r: profiles[r] * data[r] for r in renewables}, index=timesteps
    )

    units = [
        u
        for u in data.index
        if u in carrier_cost.index.get_level_values("carrier") and data.get(u, 0) > 0
    ]

    storages = ["storage"]

    co2_cost = {}
    fuel_cost = {}
    var_cost = {}
    for u in units:
        var_cost[u] = float(technology.loc["vom", u].value) * 1  # -> Money/MWh
        fuel_cost[u] = (
            float(
                (carrier_cost.loc["baseline", u].value)
                / technology.loc["efficiency", u].value
            )
            * 1
        )  # -> Money/MWh
        co2_cost[u] = (
            float(
                (carrier_cost.loc["baseline", "co2"].value)
                / technology.loc["efficiency", u].value
                * emission_factor.loc[u].value
            )
            * 1
        )  # -> Money/MWh

    # Create model
    m = ConcreteModel()

    # Variables
    def max_capacity_rule(m, t, u):
        if data.get(u):
            return (0, data[u])
        else:
            return (0, 0)

    m.p = Var(timesteps, units, within=NonNegativeReals, bounds=max_capacity_rule)

    m.excess = Var(timesteps, ["excess"], within=NonNegativeReals)
    m.shortage = Var(timesteps, ["shortage"], within=NonNegativeReals)

    m.p_storage = Var(timesteps, storages, within=Reals)
    m.c_storage = Var(
        timesteps,
        storages,
        within=NonNegativeReals,
        bounds=(0, data["storage capacity"]),
    )
    for s in storages:
        m.c_storage[timesteps[0], s].value = (
            initial_storage_level * data["storage capacity"]
        )

        m.c_storage[timesteps[0], s].fix()
        for t in timesteps:
            m.c_storage[t, s].setub(data["storage capacity"])
            m.p_storage[t, s].setub(data[s])
            m.p_storage[t, s].setlb(-data[s])

    def storage_balance(m, t, s):
        expr = 0
        if t == timesteps[0]:
            expr += m.c_storage[t, s] == m.c_storage[timesteps[-1], s]
        else:
            expr += (
                m.c_storage[t, s]
                == m.c_storage[t - pd.DateOffset(hours=1), s] - m.p_storage[t, s]
            )
        return expr

    m.storage_balance = Constraint(timesteps, storages, rule=storage_balance)

    # Constraints
    def energy_balance(m, t):
        return (
            sum(m.p[t, u] for u in units)
            + sum(m.p_storage[t, s] for s in storages)
            + m.shortage[t, "shortage"]
            == demand[t] - sum(volatile.loc[t]) + m.excess[t, "excess"]
        )

    m.energy_balance_constr = Constraint(timesteps, rule=energy_balance)

    m.total_variable_cost = Expression(
        expr=sum(m.p[t, u] * var_cost[u] for t in timesteps for u in units)
    )
    m.total_fuel_cost = Expression(
        expr=sum(m.p[t, u] * fuel_cost[u] for t in timesteps for u in units)
    )
    m.total_co2_cost = Expression(
        expr=sum(m.p[t, u] * co2_cost[u] for t in timesteps for u in units)
    )
    m.total_shortage_cost = Expression(
        expr=sum(m.shortage[t, "shortage"] * 3000e6 for t in timesteps)
    )

    # Objective function
    def obj_rule(m):
        expr = 0
        expr += m.total_variable_cost
        expr += m.total_fuel_cost
        expr += m.total_co2_cost
        expr += m.total_shortage_cost
        return expr

    m.costs = Objective(sense=minimize, rule=obj_rule)

    # m.pprint()

    # Define Solver
    opt = SolverFactory("cbc")

    # Solve the model
    opt.solve(m, tee=True)

    total_cost = pd.Series({i.name: i() for i in m.component_objects(Expression)})

    results = {
        var.name: pd.Series(
            {index: var[index].value for index in var},
            index=pd.MultiIndex.from_tuples(var, names=("timestep", "carrier")),
        ).unstack("carrier")
        for var in m.component_objects(Var)
    }
    demand - volatile

    results_df = pd.concat(
        [
            results["p"],
            results["p_storage"],
            results["excess"],
            results["shortage"],
            volatile,
            demand,
        ],
        axis=1,
    )

    results_path = os.path.join(scenario_set_path, scenario + ".csv")

    results_df.to_csv(results_path)

    # TODO: Fix path handling to store costs in file for alle scenarios
    # currently rows are appended... :-(
    # total_cost.to_csv(os.path.join(scenario_set_path,  "cost.csv"), mode="a")

    return True


if __name__ == "__main__":
    import multiprocessing as mp

    compute("BL 2017")
    # scenarios = [
    #     "Mix incl. Nuclear",
    #     "Current plans + Gas",
    #     "RE + Gas",
    #     "Medium RE + Gas",
    #     "No Imports",
    # ]
    # p = mp.Pool(5)
    # p.map(compute, scenarios)
