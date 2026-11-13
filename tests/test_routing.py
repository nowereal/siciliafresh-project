"""Test automatici del prototipo (solo libreria standard: unittest).

Esecuzione dalla cartella del progetto:  python -m unittest -v
"""

import json
import re
import shutil
import tempfile
import unittest
from itertools import permutations, product
from math import factorial
from pathlib import Path

from src.data_loader import DataError, Instance, load_deliveries, load_distances, load_instance, load_json
from src.economics import compute_costs, sensitivity, set_param, vehicle_cost
from src.routing import (InfeasibleInstanceError, VerificationError, check_instance_conditions,
                         delivery_schedule, route_distance, solve_scenario_a, solve_scenario_b, solve_tsp,
                         two_vehicle_partitions, verify_solution)
from src import visualization

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def symmetric(pairs):
    """Costruisce una matrice simmetrica da {(a, b): km}."""
    dist = {}
    for (a, b), d in pairs.items():
        dist[(a, b)] = dist[(b, a)] = d
    for a, _ in list(dist):
        dist[(a, a)] = 0
    return dist


def small_instance(capacity_a=100, capacity_b=60):
    """Istanza di 3 clienti risolvibile a mano.

    D-A 1, D-B 2, D-C 2, A-B 1, A-C 3, B-C 1.
    Giro ottimo con un veicolo: D-A-B-C-D = 1+1+1+2 = 5 km (o il suo inverso).
    """
    dist = symmetric({("D", "A"): 1, ("D", "B"): 2, ("D", "C"): 2,
                      ("A", "B"): 1, ("A", "C"): 3, ("B", "C"): 1})
    coords = {k: (i, i) for i, k in enumerate("DABC")}
    return Instance("D", ["A", "B", "C"], {k: k for k in "DABC"}, coords,
                    {"A": 30, "B": 30, "C": 30}, dist, capacity_a, capacity_b,
                    {"distance_data": {"status": "TEST"}})


def write(path, text):
    path.write_text(text, encoding="utf-8")


class TestDistance(unittest.TestCase):
    def test_route_distance(self):
        inst = small_instance()
        self.assertEqual(route_distance(["D", "A", "B", "C", "D"], inst.dist), 5)
        self.assertEqual(route_distance(["D", "C", "A", "D"], inst.dist), 2 + 3 + 1)
        self.assertEqual(route_distance(["D", "D"], inst.dist), 0)


class TestScenarioA(unittest.TestCase):
    def test_minimum_small_instance(self):
        res = solve_tsp("D", ["A", "B", "C"], small_instance().dist)
        self.assertEqual(res["distance_km"], 5)
        self.assertIn(res["route"], (["D", "A", "B", "C", "D"], ["D", "C", "B", "A", "D"]))
        self.assertEqual(res["evaluated"], 6)          # 3! permutazioni
        self.assertEqual(res["optimal_ties"], 2)       # percorso e suo inverso

    def test_real_instance_is_exhaustive(self):
        inst = load_instance(DATA)
        res = solve_scenario_a(inst)
        self.assertEqual(res["evaluated"], 120)
        brute = min(route_distance(("D",) + p + ("D",), inst.dist) for p in permutations(inst.clients))
        self.assertAlmostEqual(res["distance_km"], brute)

    def test_directional_matrix(self):
        """Con distanze asimmetriche il verso di percorrenza conta e va scelto correttamente."""
        inst = small_instance()
        inst.dist[("A", "B")] = 1     # A->B breve
        inst.dist[("B", "A")] = 9     # B->A lungo
        res = solve_tsp("D", ["A", "B", "C"], inst.dist)
        self.assertEqual(res["route"], ["D", "A", "B", "C", "D"])
        self.assertEqual(res["distance_km"], 5)
        self.assertEqual(res["optimal_ties"], 1)       # l'inverso D-C-B-A-D ora costa 2+1+9+1 = 13
        self.assertEqual(route_distance(["D", "C", "B", "A", "D"], inst.dist), 13)

    def test_loader_keeps_asymmetry(self):
        inst = load_instance(DATA)
        asym = [(a, b) for (a, b) in inst.dist if inst.dist[(a, b)] != inst.dist[(b, a)]]
        self.assertTrue(asym, "la matrice reale e direzionale: non deve essere resa simmetrica")

    def test_capacity_a_too_small(self):
        with self.assertRaises(InfeasibleInstanceError):
            solve_scenario_a(small_instance(capacity_a=50))


class TestScenarioB(unittest.TestCase):
    def test_partitions_without_duplicates(self):
        clients = ["C1", "C2", "C3", "C4", "C5"]
        parts = list(two_vehicle_partitions(clients))
        self.assertEqual(len(parts), 2 ** 4 - 1)       # 15 suddivisioni non ordinate
        unordered = {frozenset((frozenset(g1), frozenset(g2))) for g1, g2 in parts}
        self.assertEqual(len(unordered), len(parts))   # nessuna coppia scambiata ripetuta
        for g1, g2 in parts:
            self.assertTrue(g1 and g2)                 # nessun veicolo vuoto
            self.assertEqual(sorted(g1 + g2), clients) # ogni cliente esattamente una volta
        # Tutte le suddivisioni valide sono presenti: 2^5 assegnazioni ordinate - 2 vuote = 30 = 2 * 15
        self.assertEqual(2 * len(parts), 2 ** 5 - 2)

    def test_capacity_respected_and_complete(self):
        inst = load_instance(DATA)
        res = solve_scenario_b(inst)
        for load in res["loads_kg"]:
            self.assertLessEqual(load, inst.capacity_b)
        visited = [c for r in res["routes"] for c in r[1:-1]]
        self.assertEqual(sorted(visited), sorted(inst.clients))
        for r in res["routes"]:
            self.assertEqual((r[0], r[-1]), ("D", "D"))
            self.assertGreater(len(r), 2)

    def test_optimal_against_independent_bruteforce(self):
        """Confronto con una enumerazione indipendente su assegnazioni ORDINATE."""
        inst = load_instance(DATA)
        best = None
        for assign in product((0, 1), repeat=len(inst.clients)):
            groups = [[c for c, v in zip(inst.clients, assign) if v == k] for k in (0, 1)]
            if not all(groups):
                continue
            if any(sum(inst.demand[c] for c in g) > inst.capacity_b for g in groups):
                continue
            total = sum(min(route_distance(("D",) + p + ("D",), inst.dist) for p in permutations(g))
                        for g in groups)
            best = total if best is None else min(best, total)
        self.assertAlmostEqual(solve_scenario_b(inst)["distance_km"], best)

    def test_combination_count_formula(self):
        """Combinazioni valutate = somma di k! * (n-k)! sulle sole suddivisioni ammissibili."""
        inst = load_instance(DATA)
        res = solve_scenario_b(inst)
        feasible = [p for p in res["partitions"] if p["feasible"]]
        self.assertEqual(len(feasible), res["feasible_partitions"])
        expected = sum(factorial(len(p["group1"])) * factorial(len(p["group2"])) for p in feasible)
        self.assertEqual(res["evaluated"], expected)
        for p in res["partitions"]:
            self.assertEqual(p["feasible"], p["load1"] <= inst.capacity_b and p["load2"] <= inst.capacity_b)

    def test_small_instance_by_hand(self):
        # Capacita 60 kg: al massimo 2 clienti per veicolo. Suddivisioni ammissibili:
        # {A}{B,C}: 2 + (2+1+2)=7 ; {A,B}{C}: (1+1+2)+4=8 ; {A,C}{B}: (1+3+2)+4=10  -> ottimo 7
        res = solve_scenario_b(small_instance())
        self.assertEqual(res["distance_km"], 7)
        self.assertEqual(res["partitions_examined"], 3)
        self.assertEqual(res["feasible_partitions"], 3)

    def test_infeasible_instance(self):
        with self.assertRaises(InfeasibleInstanceError):
            solve_scenario_b(small_instance(capacity_b=25))   # nessun cliente entra in un veicolo

    def test_instance_conditions(self):
        checks = check_instance_conditions(load_instance(DATA))
        self.assertTrue(all(c["passed"] for c in checks), checks)
        # capacita B sufficiente per tutto: la condizione 2 deve fallire
        checks = check_instance_conditions(small_instance(capacity_b=200))
        self.assertFalse(checks[1]["passed"])


class TestDeliverySchedule(unittest.TestCase):
    """Sequenza delle consegne: carico iniziale, consegne e carico residuo."""

    def setUp(self):
        self.inst = load_instance(DATA)
        self.a = solve_scenario_a(self.inst)
        self.b = solve_scenario_b(self.inst)
        self.schedules = [self.a["schedule"]] + self.b["schedules"]

    def test_initial_load_is_sum_of_deliveries(self):
        for s in self.schedules:
            delivered = sum(step["delivered_kg"] for step in s["steps"])
            self.assertAlmostEqual(s["initial_load_kg"], delivered)
            self.assertLessEqual(s["initial_load_kg"], s["capacity_kg"])
        self.assertEqual(self.a["schedule"]["initial_load_kg"], self.a["load_kg"])
        self.assertEqual([s["initial_load_kg"] for s in self.b["schedules"]], self.b["loads_kg"])

    def test_residual_decreases_and_ends_at_zero(self):
        for s in self.schedules:
            steps = s["steps"]
            self.assertEqual(steps[0]["kind"], "partenza")
            self.assertEqual(steps[-1]["kind"], "rientro")
            for prev, cur in zip(steps, steps[1:]):
                self.assertAlmostEqual(cur["residual_kg"], prev["residual_kg"] - cur["delivered_kg"])
                self.assertGreaterEqual(cur["residual_kg"], 0)
                if cur["kind"] == "consegna":
                    self.assertLess(cur["residual_kg"], prev["residual_kg"])
            self.assertEqual(steps[-1]["residual_kg"], 0)
            self.assertEqual(steps[-1]["delivered_kg"], 0)

    def test_each_client_receives_its_demand_once(self):
        received = {}
        for s in [self.a["schedule"]]:
            for step in s["steps"]:
                if step["kind"] == "consegna":
                    received[step["stop"]] = received.get(step["stop"], 0) + step["delivered_kg"]
        self.assertEqual(received, self.inst.demand)
        received_b = {}
        for s in self.b["schedules"]:
            for step in s["steps"]:
                if step["kind"] == "consegna":
                    self.assertNotIn(step["stop"], received_b)
                    received_b[step["stop"]] = step["delivered_kg"]
        self.assertEqual(received_b, self.inst.demand)
        self.assertEqual(sum(received_b.values()), 1500)

    def test_distances_follow_matrix(self):
        for s in self.schedules:
            for prev, cur in zip(s["steps"], s["steps"][1:]):
                self.assertEqual(cur["leg_km"], self.inst.dist[(prev["stop"], cur["stop"])])
        self.assertAlmostEqual(self.a["schedule"]["steps"][-1]["cumulative_km"], self.a["distance_km"])

    def test_hand_example(self):
        inst = small_instance()
        s = delivery_schedule(["D", "A", "B", "D"], inst.demand, inst.dist, 60)
        self.assertEqual([st["residual_kg"] for st in s["steps"]], [60, 30, 0, 0])
        self.assertEqual([st["delivered_kg"] for st in s["steps"]], [0, 30, 30, 0])
        with self.assertRaises(VerificationError):
            delivery_schedule(["D", "A", "B", "C", "D"], inst.demand, inst.dist, 60)   # 90 kg > 60


class TestConfiguration(unittest.TestCase):
    """La configurazione geografica concordata non deve cambiare per errore."""

    def test_depot_and_clients(self):
        inst = load_instance(DATA)
        self.assertEqual(inst.names[inst.depot], "San Pier Marina")
        self.assertEqual(sorted(inst.names[c] for c in inst.clients),
                         sorted(["Milazzo", "Monforte Marina", "Torregrotta", "Venetico Marina", "Spadafora"]))
        self.assertEqual(sum(inst.demand.values()), 1500)

    def test_distance_matrix_complete(self):
        inst = load_instance(DATA)
        ids = [inst.depot] + inst.clients
        pairs = [(a, b) for a in ids for b in ids if a != b]
        self.assertEqual(len(pairs), 30)
        for a, b in pairs:
            self.assertGreater(inst.dist[(a, b)], 0)
        for a in ids:
            self.assertEqual(inst.dist[(a, a)], 0)
        # la matrice coincide con la risposta OSRM documentata (arrotondata ai 10 m)
        source = json.loads((DATA / "distances_source.json").read_text(encoding="utf-8"))
        osrm = source["response"]["distances"]
        for i, a in enumerate(source["ids"]):
            for j, b in enumerate(source["ids"]):
                self.assertAlmostEqual(inst.dist[(a, b)], round(osrm[i][j] / 1000, 2), places=6)


class TestGraphLayout(unittest.TestCase):
    """Disposizione schematica dei nodi: coerente con la geografia e uguale nei due scenari."""

    def test_order_follows_geography(self):
        inst = load_instance(DATA)
        layout = visualization.schematic_layout(inst)
        by_x = [inst.names[i] for i in sorted(layout, key=lambda i: layout[i][0])]
        self.assertEqual(by_x, ["Milazzo", "San Pier Marina", "Monforte Marina", "Torregrotta",
                                "Venetico Marina", "Spadafora"])
        by_lon = sorted(layout, key=lambda i: inst.geo[i][1])
        self.assertEqual(sorted(layout, key=lambda i: layout[i][0]), by_lon)
        by_lat = sorted(layout, key=lambda i: -inst.geo[i][0])            # da nord a sud
        self.assertEqual(sorted(layout, key=lambda i: layout[i][1]), by_lat)
        # Monforte Marina circa alla stessa altezza del deposito
        self.assertLess(abs(layout["C2"][1] - layout["D"][1]), 0.15)

    def test_same_node_positions_in_both_scenarios(self):
        html = (ROOT / "output" / "index.html").read_text(encoding="utf-8")
        graph_a = html.split('data-scenario-graph="A"')[1].split('data-scenario-graph="B"')[0]
        graph_b = html.split('data-scenario-graph="B"')[1].split("</figure>")[0]
        pattern = r'<g class="g-node"[^>]*>(?:<rect x="([\d.]+)" y="([\d.]+)"|<circle cx="([\d.]+)" cy="([\d.]+)")'
        self.assertEqual(re.findall(pattern, graph_a), re.findall(pattern, graph_b))
        self.assertEqual(len(re.findall(pattern, graph_a)), 6)


class TestVehicleColors(unittest.TestCase):
    """I due veicoli hanno colori distinti, usati in modo coerente in grafo, legenda e schede."""

    def test_colors_in_page(self):
        css = (ROOT / "output" / "styles.css").read_text(encoding="utf-8")
        html = (ROOT / "output" / "index.html").read_text(encoding="utf-8")
        v1 = re.search(r"--v1:\s*(#[0-9A-Fa-f]{6})", css).group(1)
        v2 = re.search(r"--v2:\s*(#[0-9A-Fa-f]{6})", css).group(1)
        self.assertNotEqual(v1.lower(), v2.lower())
        self.assertEqual(v1.upper(), visualization.VEHICLE_COLORS[0].upper())
        self.assertEqual(v2.upper(), visualization.VEHICLE_COLORS[1].upper())
        # i percorsi del grafo B e la legenda usano le stesse variabili dei veicoli
        graph_b = html.split('data-scenario-graph="B"')[1].split("</figure>")[0]
        self.assertIn('class="g-route" style="--vc:var(--v1)"', graph_b)
        self.assertIn('class="g-route" style="--vc:var(--v2)"', graph_b)
        self.assertNotIn("stroke-dasharray=\"8 7\"", graph_b)   # niente tratteggio come codifica
        legend = graph_b.split('class="legend"')[1]
        self.assertIn("var(--v1)", legend)
        self.assertIn("var(--v2)", legend)


class TestVerification(unittest.TestCase):
    def test_detects_errors(self):
        inst = small_instance()
        self.assertTrue(verify_solution([["D", "A", "B", "C", "D"]], inst, 100))
        with self.assertRaises(VerificationError):
            verify_solution([["D", "A", "B", "D"]], inst, 100)                    # C escluso
        with self.assertRaises(VerificationError):
            verify_solution([["D", "A", "B", "D"], ["D", "B", "C", "D"]], inst, 100)  # B due volte
        with self.assertRaises(VerificationError):
            verify_solution([["A", "B", "C", "D"]], inst, 100)                    # non parte dal deposito
        with self.assertRaises(VerificationError):
            verify_solution([["D", "A", "B", "C", "D"]], inst, 60)                # capacita superata


class TestEconomics(unittest.TestCase):
    def setUp(self):
        self.inst = load_instance(DATA)
        self.costs = load_json(DATA / "costs.json")
        self.a = solve_scenario_a(self.inst)
        self.b = solve_scenario_b(self.inst)

    def test_vehicle_cost_by_hand(self):
        vehicle = {"fixed_cost_eur_per_day": 50, "fuel_consumption_l_per_km": 0.1,
                   "other_variable_cost_eur_per_km": 0.2}
        common = {"fuel_price_eur_per_l": 2.0, "driver_cost_eur_per_h": 20,
                  "average_speed_kmh": 40, "service_time_min_per_stop": 15}
        c = vehicle_cost(40, 2, vehicle, common)   # 1 h guida + 0,5 h fermate
        self.assertAlmostEqual(c["fuel"], 8.0)
        self.assertAlmostEqual(c["other_km"], 8.0)
        self.assertAlmostEqual(c["hours"], 1.5)
        self.assertAlmostEqual(c["driver"], 30.0)
        self.assertAlmostEqual(c["total"], 96.0)

    def test_costs_consistency(self):
        c = compute_costs(self.a, self.b, self.costs)
        for key in ("A", "B"):
            t = c[key]["totals"]
            self.assertAlmostEqual(t["total"], t["fixed"] + t["fuel"] + t["other_km"] + t["driver"])
        self.assertAlmostEqual(c["B"]["totals"]["distance_km"], self.b["distance_km"])
        self.assertAlmostEqual(c["B"]["totals"]["fixed"],
                               2 * self.costs["vehicle_types"]["scenario_B"]["fixed_cost_eur_per_day"])
        comp = c["comparison"]
        self.assertAlmostEqual(comp["abs_diff"], abs(comp["cost_b"] - comp["cost_a"]))
        self.assertAlmostEqual(comp["pct_diff_vs_a"], (comp["cost_b"] - comp["cost_a"]) / comp["cost_a"] * 100)
        self.assertEqual(comp["cheaper"], "A" if comp["cost_a"] < comp["cost_b"] else "B")

    def test_sensitivity_and_breakeven(self):
        for spec in self.costs["sensitivity"]:
            s = sensitivity(self.a, self.b, self.costs, spec)
            self.assertAlmostEqual(s["rows"][0]["value"], spec["min"])
            self.assertAlmostEqual(s["rows"][-1]["value"], spec["max"])
            if s["breakeven"] is not None:
                varied = json.loads(json.dumps(self.costs))
                set_param(varied, spec["parameter"], s["breakeven"])
                comp = compute_costs(self.a, self.b, varied)["comparison"]
                self.assertAlmostEqual(comp["cost_a"], comp["cost_b"], places=6)


class TestInvalidData(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_missing_and_invalid_values(self):
        ids = ["D", "C1"]
        cases = {
            "from,D,C1\nD,0,\nC1,5,0\n": "mancante",
            "from,D,C1\nD,0,abc\nC1,5,0\n": "numerico",
            "from,D,C1\nD,0,-3\nC1,5,0\n": "negativo",
            "from,D,C1\nD,0,5\n": "mancanti",
            "from,D\nD,0\nC1,5\n": "colonne",
        }
        for text, expected in cases.items():
            write(self.tmp / "d.csv", text)
            with self.assertRaises(DataError, msg=text) as ctx:
                load_distances(self.tmp / "d.csv", ids)
            self.assertIn(expected, str(ctx.exception))

    def test_missing_demand(self):
        write(self.tmp / "q.csv", "id,demand_kg\nC1,100\n")
        with self.assertRaises(DataError):
            load_deliveries(self.tmp / "q.csv", ["C1", "C2"])
        write(self.tmp / "q.csv", "id,demand_kg\nC1,0\nC2,10\n")
        with self.assertRaises(DataError):
            load_deliveries(self.tmp / "q.csv", ["C1", "C2"])

    def test_missing_file(self):
        with self.assertRaises(DataError):
            load_instance(self.tmp)


class TestHtmlMatchesResults(unittest.TestCase):
    """La pagina generata deve riportare esattamente i valori di results.json."""

    def test_html_values(self):
        import main
        tmp = Path(tempfile.mkdtemp())
        try:
            main.run(DATA, tmp)
            results = json.loads((tmp / "results.json").read_text(encoding="utf-8"))
            html = (tmp / "index.html").read_text(encoding="utf-8")
        finally:
            shutil.rmtree(tmp)
        shown = dict(re.findall(r'<span data-key="([^"]+)">(.*?)</span>', html))
        a, b = results["scenario_A"], results["scenario_B"]
        comp = results["costs"]["comparison"]
        expected = {
            "a.distance_km": visualization.km(a["distance_km"]),
            "a.evaluated": str(a["evaluated"]),
            "a.load_kg": visualization.num(a["load_kg"], 0),
            "a.cost_total": visualization.eur(results["costs"]["A"]["totals"]["total"]),
            "b.distance_km": visualization.km(b["distance_km"]),
            "b.partitions_examined": str(b["partitions_examined"]),
            "b.feasible_partitions": str(b["feasible_partitions"]),
            "b.evaluated": str(b["evaluated"]),
            "b.v1.distance_km": visualization.km(b["distances_km"][0]),
            "b.v2.distance_km": visualization.km(b["distances_km"][1]),
            "b.v1.load_kg": visualization.num(b["loads_kg"][0], 0),
            "b.v2.load_kg": visualization.num(b["loads_kg"][1], 0),
            "b.cost_total": visualization.eur(results["costs"]["B"]["totals"]["total"]),
            "cmp.abs_diff": visualization.eur(comp["abs_diff"]),
            "cmp.pct_diff": visualization.num(comp["pct_diff_vs_a"]) + "&nbsp;%",
            "dist.pct_diff": visualization.num(results["distance_comparison"]["pct_diff_vs_a"]) + "&nbsp;%",
            "total_demand_kg": visualization.num(a["load_kg"], 0),   # nello Scenario A un veicolo porta tutto
        }
        for key, value in expected.items():
            self.assertEqual(shown.get(key), value, key)
        self.assertIn(f"Scenario {comp['cheaper']}", shown["cmp.cheaper"])

    def test_local_links_exist(self):
        """Ogni file locale richiamato dalla pagina (CSS, JS, JSON) deve esistere in output/."""
        html = (ROOT / "output" / "index.html").read_text(encoding="utf-8")
        refs = re.findall(r'(?:href|src)="([^"#:]+)"', html)
        self.assertIn("styles.css", refs)
        self.assertIn("app.js", refs)
        for ref in refs:
            self.assertTrue((ROOT / "output" / ref).exists(), f"file mancante: {ref}")


if __name__ == "__main__":
    unittest.main()
