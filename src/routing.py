"""Ottimizzazione dei percorsi mediante enumerazione completa.

Scenario A (TSP): un veicolo visita tutti i clienti; si provano tutte le n!
permutazioni dei clienti.

Scenario B (VRP con capacita, 2 veicoli identici): si provano tutte le
suddivisioni dei clienti in due gruppi non vuoti e, per ogni suddivisione che
rispetta le capacita, tutte le coppie di permutazioni dei due percorsi.

Nessuna euristica: il risultato e ottimo per costruzione, perche ogni
soluzione ammissibile viene valutata.
"""

from itertools import permutations


class InfeasibleInstanceError(Exception):
    """L'istanza non ammette alcuna soluzione che rispetti i vincoli."""


class VerificationError(AssertionError):
    """Una soluzione calcolata viola un vincolo (non dovrebbe mai accadere)."""


# ---------------------------------------------------------------------------
# Funzioni di base
# ---------------------------------------------------------------------------

def route_distance(route, dist):
    """Distanza totale di un percorso espresso come sequenza di localita.

    Il percorso deve gia includere il deposito all'inizio e alla fine,
    ad esempio ("D", "C1", "C3", "D").
    """
    return sum(dist[(route[i], route[i + 1])] for i in range(len(route) - 1))


def route_load(route, demand):
    """Carico iniziale (kg) di un percorso: somma delle quantita da consegnare ai clienti visitati."""
    return sum(demand.get(stop, 0) for stop in route)


def two_vehicle_partitions(clients):
    """Genera tutte le suddivisioni dei clienti in due gruppi NON vuoti.

    I veicoli sono identici, quindi le coppie (G1, G2) e (G2, G1) sono la
    stessa soluzione. Per contarle una sola volta si fissa il primo cliente
    nel gruppo del veicolo 1: ogni suddivisione non ordinata compare
    esattamente una volta. Con n clienti si ottengono 2^(n-1) - 1 suddivisioni
    (15 per n = 5).
    """
    first, others = clients[0], clients[1:]
    n_others = len(others)
    for mask in range(2 ** n_others):
        group1 = [first] + [others[i] for i in range(n_others) if mask & (1 << i)]
        group2 = [others[i] for i in range(n_others) if not mask & (1 << i)]
        if group2:  # esclude il caso in cui il veicolo 2 resta inutilizzato
            yield group1, group2


# ---------------------------------------------------------------------------
# Scenario A - un veicolo (TSP)
# ---------------------------------------------------------------------------

def solve_tsp(depot, clients, dist):
    """Enumera tutte le permutazioni e restituisce il percorso piu breve.

    In caso di parita (ad es. il percorso inverso con distanze simmetriche)
    si tiene il primo trovato, cosi il risultato e deterministico.
    """
    best_route, best_km, evaluated, all_km = None, None, 0, []
    for perm in permutations(clients):
        route = (depot,) + perm + (depot,)
        km = route_distance(route, dist)
        evaluated += 1
        all_km.append(km)
        if best_km is None or km < best_km:
            best_route, best_km = route, km
    if best_route is None:
        raise InfeasibleInstanceError("Nessun cliente da servire")
    return {
        "route": list(best_route),
        "distance_km": best_km,
        "evaluated": evaluated,
        "optimal_ties": sum(1 for km in all_km if abs(km - best_km) < 1e-9),
        "min_check": min(all_km),
    }


def solve_scenario_a(instance):
    total = sum(instance.demand.values())
    if total > instance.capacity_a:
        raise InfeasibleInstanceError(
            f"Scenario A non risolvibile: domanda totale {total:g} kg > capacita {instance.capacity_a:g} kg")
    result = solve_tsp(instance.depot, instance.clients, instance.dist)
    result["load_kg"] = route_load(result["route"], instance.demand)
    result["capacity_kg"] = instance.capacity_a
    verify_solution([result["route"]], instance, instance.capacity_a)
    if abs(result["distance_km"] - result["min_check"]) > 1e-9:
        raise VerificationError("Scenario A: il risultato non coincide con il minimo enumerato")
    # load_kg = carico iniziale alla partenza dal deposito (somma delle consegne del giro)
    result["schedule"] = delivery_schedule(result["route"], instance.demand, instance.dist, instance.capacity_a)
    return result


# ---------------------------------------------------------------------------
# Scenario B - due veicoli identici (VRP con capacita)
# ---------------------------------------------------------------------------

def solve_scenario_b(instance):
    depot, dist, demand, cap = instance.depot, instance.dist, instance.demand, instance.capacity_b
    partitions_examined = 0
    feasible_partitions = 0
    combinations_evaluated = 0
    best = None
    all_totals = []
    partition_log = []  # riepilogo di ogni suddivisione, mostrato nella pagina HTML

    for group1, group2 in two_vehicle_partitions(instance.clients):
        partitions_examined += 1
        load1 = sum(demand[c] for c in group1)
        load2 = sum(demand[c] for c in group2)
        feasible = load1 <= cap and load2 <= cap
        entry = {"group1": group1, "group2": group2, "load1": load1, "load2": load2,
                 "feasible": feasible, "best_km": None}
        partition_log.append(entry)
        if not feasible:
            continue  # vincolo di capacita violato: la suddivisione viene scartata
        feasible_partitions += 1

        # Tutte le coppie di permutazioni dei due percorsi
        for p1 in permutations(group1):
            r1 = (depot,) + p1 + (depot,)
            d1 = route_distance(r1, dist)
            for p2 in permutations(group2):
                r2 = (depot,) + p2 + (depot,)
                d2 = route_distance(r2, dist)
                total = d1 + d2
                combinations_evaluated += 1
                all_totals.append(total)
                if entry["best_km"] is None or total < entry["best_km"]:
                    entry["best_km"] = total
                if best is None or total < best["distance_km"]:
                    best = {"routes": [list(r1), list(r2)], "distances_km": [d1, d2],
                            "distance_km": total}

    if best is None:
        raise InfeasibleInstanceError(
            f"Scenario B non risolvibile: nessuna suddivisione rispetta la capacita di {cap:g} kg per veicolo")

    best["loads_kg"] = [route_load(r, demand) for r in best["routes"]]
    best["capacity_kg"] = cap
    best["partitions_examined"] = partitions_examined
    best["feasible_partitions"] = feasible_partitions
    best["evaluated"] = combinations_evaluated
    best["optimal_ties"] = sum(1 for t in all_totals if abs(t - best["distance_km"]) < 1e-9)
    best["min_check"] = min(all_totals)
    best["partitions"] = partition_log

    verify_solution(best["routes"], instance, cap)
    if abs(best["distance_km"] - best["min_check"]) > 1e-9:
        raise VerificationError("Scenario B: il risultato non coincide con il minimo enumerato")
    if any(len(r) <= 2 for r in best["routes"]):
        raise VerificationError("Scenario B: un veicolo risulta inutilizzato")
    # loads_kg = carico iniziale di ciascun veicolo alla partenza dal deposito
    best["schedules"] = [delivery_schedule(r, demand, dist, cap) for r in best["routes"]]
    return best


# ---------------------------------------------------------------------------
# Sequenza delle consegne e carico residuo
# ---------------------------------------------------------------------------

def delivery_schedule(route, demand, dist, capacity):
    """Ricostruisce la sequenza delle consegne di un percorso gia ottimizzato.

    Il problema e di distribuzione: il veicolo parte dal deposito con la merce di
    tutti i clienti assegnati (carico iniziale), a ogni fermata scarica la quantita
    richiesta dal cliente e il carico residuo diminuisce; al rientro e zero.
    La funzione non ottimizza nulla: usa l'ordine di visita prodotto dall'algoritmo.
    """
    initial = route_load(route, demand)
    if initial > capacity:
        raise VerificationError(f"Carico iniziale {initial:g} kg oltre la capacita {capacity:g} kg")
    steps = [{"stop": route[0], "kind": "partenza", "delivered_kg": 0, "residual_kg": initial,
              "leg_km": 0.0, "cumulative_km": 0.0}]
    residual, cumulative = initial, 0.0
    for a, b in zip(route, route[1:]):
        leg = dist[(a, b)]
        cumulative += leg
        delivered = demand.get(b, 0) if b != route[0] else 0
        residual -= delivered
        if residual < -1e-9:
            raise VerificationError(f"Carico residuo negativo dopo {b}")
        steps.append({"stop": b, "kind": "rientro" if b == route[0] else "consegna",
                      "delivered_kg": delivered, "residual_kg": residual,
                      "leg_km": leg, "cumulative_km": cumulative})
    if abs(residual) > 1e-9:
        raise VerificationError(f"Carico residuo al rientro diverso da zero: {residual:g} kg")
    return {"initial_load_kg": initial, "capacity_kg": capacity, "steps": steps}


# ---------------------------------------------------------------------------
# Verifiche automatiche
# ---------------------------------------------------------------------------

def verify_solution(routes, instance, capacity):
    """Controlla i vincoli di una soluzione; solleva VerificationError se violati.

    - ogni percorso parte e termina al deposito;
    - ogni cliente e servito esattamente una volta;
    - nessun cliente e escluso;
    - nessun veicolo supera la capacita.
    """
    visits = []
    for route in routes:
        if route[0] != instance.depot or route[-1] != instance.depot:
            raise VerificationError(f"Il percorso {route} non parte/termina al deposito")
        if instance.depot in route[1:-1]:
            raise VerificationError(f"Il percorso {route} ripassa dal deposito")
        load = route_load(route, instance.demand)
        if load > capacity:
            raise VerificationError(f"Il percorso {route} supera la capacita ({load:g} > {capacity:g} kg)")
        visits.extend(route[1:-1])
    duplicates = sorted({c for c in visits if visits.count(c) > 1})
    if duplicates:
        raise VerificationError(f"Clienti serviti piu di una volta: {duplicates}")
    missing = sorted(set(instance.clients) - set(visits))
    if missing:
        raise VerificationError(f"Clienti non serviti: {missing}")
    unknown = sorted(set(visits) - set(instance.clients))
    if unknown:
        raise VerificationError(f"Localita sconosciute nei percorsi: {unknown}")
    return True


def check_instance_conditions(instance):
    """Verifica le condizioni richieste dalla traccia sulle quantita e capacita.

    Restituisce una lista di controlli (descrizione, esito, dettaglio).
    La condizione 3 (esiste una suddivisione ammissibile) e verificata
    per enumerazione sulle stesse suddivisioni usate dallo Scenario B.
    """
    total = sum(instance.demand.values())
    feasible_split = any(
        sum(instance.demand[c] for c in g1) <= instance.capacity_b
        and sum(instance.demand[c] for c in g2) <= instance.capacity_b
        for g1, g2 in two_vehicle_partitions(instance.clients))
    return [
        {"check": "Il veicolo dello Scenario A trasporta tutte le consegne",
         "passed": total <= instance.capacity_a,
         "detail": f"domanda totale {total:g} kg ≤ capacità {instance.capacity_a:g} kg"},
        {"check": "Nessun veicolo dello Scenario B trasporta da solo tutte le consegne",
         "passed": total > instance.capacity_b,
         "detail": f"domanda totale {total:g} kg > capacità {instance.capacity_b:g} kg"},
        {"check": "Esiste almeno una ripartizione ammissibile tra i due veicoli",
         "passed": feasible_split,
         "detail": "verificato enumerando tutte le ripartizioni"},
        {"check": "Ogni singola consegna è trasportabile da un veicolo dello Scenario B",
         "passed": max(instance.demand.values()) <= instance.capacity_b,
         "detail": f"consegna massima {max(instance.demand.values()):g} kg ≤ {instance.capacity_b:g} kg"},
    ]
