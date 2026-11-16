"""Modello economico dei due scenari e analisi di sensibilita.

Costo di un veicolo in una giornata di consegne:

    costo = costo fisso giornaliero
          + km * consumo (l/km) * prezzo carburante (EUR/l)
          + km * altri costi variabili (EUR/km: pneumatici, manutenzione, usura)
          + ore di lavoro * costo orario autista

    ore di lavoro = km / velocita media + n. fermate * tempo di servizio

Il costo e lineare in ogni prezzo unitario: per questo il punto di pareggio
tra i due scenari, se esiste, si calcola in forma chiusa.
"""

import copy


def vehicle_cost(distance_km, n_stops, vehicle, common):
    """Scompone il costo giornaliero di un singolo veicolo."""
    speed = common["average_speed_kmh"]
    if speed <= 0:
        raise ValueError("La velocita media deve essere positiva")
    hours = distance_km / speed + n_stops * common["service_time_min_per_stop"] / 60.0
    parts = {
        "fixed": vehicle["fixed_cost_eur_per_day"],
        "fuel": distance_km * vehicle["fuel_consumption_l_per_km"] * common["fuel_price_eur_per_l"],
        "other_km": distance_km * vehicle["other_variable_cost_eur_per_km"],
        "driver": hours * common["driver_cost_eur_per_h"],
    }
    parts["total"] = sum(parts.values())
    parts["hours"] = hours
    parts["distance_km"] = distance_km
    return parts


def scenario_cost(routes, vehicle, common):
    """Somma i costi dei veicoli di uno scenario. routes include il deposito."""
    vehicles = []
    for route, km in routes:
        vehicles.append(vehicle_cost(km, len(route) - 2, vehicle, common))
    keys = ("fixed", "fuel", "other_km", "driver", "total", "hours", "distance_km")
    totals = {k: sum(v[k] for v in vehicles) for k in keys}
    return {"vehicles": vehicles, "totals": totals}


def compare(cost_a, cost_b):
    """Confronto tra il costo totale dello Scenario A e quello dello Scenario B."""
    diff = cost_b - cost_a
    return {
        "cost_a": cost_a,
        "cost_b": cost_b,
        "abs_diff": abs(diff),
        "diff_b_minus_a": diff,
        "pct_diff_vs_a": diff / cost_a * 100 if cost_a else None,
        "cheaper": "A" if cost_a < cost_b else ("B" if cost_b < cost_a else "pari"),
    }


def compute_costs(result_a, result_b, costs):
    """Costi complessivi dei due scenari a partire dai percorsi ottimali."""
    common = costs["common"]
    a = scenario_cost([(result_a["route"], result_a["distance_km"])],
                      costs["vehicle_types"]["scenario_A"], common)
    b = scenario_cost(list(zip(result_b["routes"], result_b["distances_km"])),
                      costs["vehicle_types"]["scenario_B"], common)
    return {"A": a, "B": b, "comparison": compare(a["totals"]["total"], b["totals"]["total"])}


def _frange(start, stop, step):
    values, i = [], 0
    while True:
        v = round(start + i * step, 10)
        if v > stop + 1e-9:
            break
        values.append(v)
        i += 1
    return values


def _param_path(costs, param):
    """Un parametro e un nome di 'common' (es. fuel_price_eur_per_l) oppure un
    percorso puntato (es. vehicle_types.scenario_A.fixed_cost_eur_per_day)."""
    path = param.split(".") if "." in param else ["common", param]
    node = costs
    for key in path[:-1]:
        node = node.get(key, {}) if isinstance(node, dict) else {}
    if not isinstance(node, dict) or path[-1] not in node:
        raise KeyError(f"Parametro di sensibilita sconosciuto: {param}")
    return path


def get_param(costs, param):
    node = costs
    for key in _param_path(costs, param):
        node = node[key]
    return node


def set_param(costs, param, value):
    path = _param_path(costs, param)
    node = costs
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


def sensitivity(result_a, result_b, costs, spec):
    """Ripete il confronto facendo variare un solo prezzo unitario.

    I percorsi restano quelli ottimali in distanza: si studia come cambia la
    convenienza economica, non si ri-ottimizza il percorso sul costo.
    """
    param = spec["parameter"]
    _param_path(costs, param)  # verifica che il parametro esista

    def totals_at(value):
        varied = copy.deepcopy(costs)
        set_param(varied, param, value)
        c = compute_costs(result_a, result_b, varied)
        return c["A"]["totals"]["total"], c["B"]["totals"]["total"]

    rows = []
    for value in _frange(spec["min"], spec["max"], spec["step"]):
        ca, cb = totals_at(value)
        rows.append({"value": value, "cost_a": ca, "cost_b": cb, "diff_b_minus_a": cb - ca,
                     "cheaper": "A" if ca < cb else ("B" if cb < ca else "pari")})

    # Pareggio: la differenza B - A e una retta nel parametro, diff(p) = q + m*p
    d0 = (lambda t: t[1] - t[0])(totals_at(0.0))
    d1 = (lambda t: t[1] - t[0])(totals_at(1.0))
    slope = d1 - d0
    breakeven = None if abs(slope) < 1e-12 else -d0 / slope
    in_range = breakeven is not None and spec["min"] <= breakeven <= spec["max"]
    return {
        "parameter": param,
        "label": spec["label"],
        "base_value": get_param(costs, param),
        "rows": rows,
        "breakeven": breakeven,
        "breakeven_in_range": in_range,
        "breakeven_meaningful": breakeven is not None and breakeven > 0,
    }
