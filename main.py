"""SiciliaFresh - pianificazione e confronto economico delle consegne.

Esecuzione:  python main.py            (calcola, salva i risultati e apre la pagina)
             python main.py --no-open  (non apre il browser)

Legge i dati da data/, risolve i due scenari con enumerazione completa,
calcola costi e sensibilita, scrive output/results.json e output/index.html.
"""

import argparse
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from src.data_loader import DataError, load_instance, load_json
from src.economics import compute_costs, sensitivity
from src.routing import (InfeasibleInstanceError, VerificationError, check_instance_conditions,
                         solve_scenario_a, solve_scenario_b)
from src.visualization import build_html

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"


def run(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    """Esegue l'intera analisi e restituisce (instance, results)."""
    instance = load_instance(data_dir)
    costs_cfg = load_json(Path(data_dir) / "costs.json")

    checks = check_instance_conditions(instance)
    failed = [c for c in checks if not c["passed"]]
    if failed:
        raise InfeasibleInstanceError("Istanza non conforme alla traccia: " +
                                      "; ".join(f"{c['check']} ({c['detail']})" for c in failed))

    result_a = solve_scenario_a(instance)
    result_b = solve_scenario_b(instance)
    costs = compute_costs(result_a, result_b, costs_cfg)
    sens = [sensitivity(result_a, result_b, costs_cfg, spec) for spec in costs_cfg["sensitivity"]]

    d_a, d_b = result_a["distance_km"], result_b["distance_km"]
    results = {
        # Data di riferimento dell'analisi da config.json; in assenza, data e ora di esecuzione
        "generated_at": instance.config.get("analysis_date") or datetime.now().strftime("%d/%m/%Y %H:%M"),
        "distance_data_status": instance.config["distance_data"]["status"],
        "instance_checks": checks,
        "scenario_A": result_a,
        "scenario_B": result_b,
        "distance_comparison": {"distance_a_km": d_a, "distance_b_km": d_b,
                                "diff_km": d_b - d_a, "pct_diff_vs_a": (d_b - d_a) / d_a * 100},
        "costs": costs,
        "sensitivity": sens,
    }
    # Riepilogo del controllo indipendente delle distanze (tools/check_distances.py), se presente
    check_file = Path(data_dir) / "distances_check.json"
    if check_file.exists():
        check = load_json(check_file)
        results["distance_check"] = {"service": check["service"], "retrieved_at": check["retrieved_at"],
                                     **check["summary"]}

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "results.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    with open(output_dir / "index.html", "w", encoding="utf-8") as handle:
        handle.write(build_html(instance, results, costs_cfg))
    return instance, results


def print_schedule(schedule, names):
    """Sequenza delle consegne: quantita consegnata e carico residuo dopo ogni fermata."""
    for step in schedule["steps"][1:]:
        if step["kind"] == "consegna":
            print(f"             - {names[step['stop']]}: consegna {step['delivered_kg']:g} kg, "
                  f"residuo {step['residual_kg']:g} kg")
        else:
            print(f"             - rientro al deposito con {step['residual_kg']:g} kg a bordo")


def print_summary(instance, results):
    n = instance.names
    a, b = results["scenario_A"], results["scenario_B"]
    comp, dist = results["costs"]["comparison"], results["distance_comparison"]

    def path(route):
        return " -> ".join(n[s] for s in route)

    print("=" * 72)
    print("SiciliaFresh - risultati")
    if results["distance_data_status"] != "VERIFIED":
        print("ATTENZIONE: distanze SIMULATE, da sostituire con distanze stradali reali.")
    print("=" * 72)
    print("\nVerifiche dell'istanza:")
    for c in results["instance_checks"]:
        print(f"  [{'OK' if c['passed'] else 'NO'}] {c['check']} - {c['detail']}")

    print("\nSCENARIO A - un veicolo")
    print(f"  Permutazioni esaminate:        {a['evaluated']} (tutte ammissibili)")
    print(f"  Percorso ottimale:             {path(a['route'])}")
    print(f"  Distanza totale:               {a['distance_km']:.2f} km")
    print(f"  Carico iniziale:               {a['load_kg']:g} / {a['capacity_kg']:g} kg")
    print_schedule(a["schedule"], n)

    print("\nSCENARIO B - due veicoli identici")
    print(f"  Ripartizioni esaminate:        {b['partitions_examined']}")
    print(f"  Ripartizioni ammissibili:      {b['feasible_partitions']}")
    print(f"  Combinazioni di percorsi:      {b['evaluated']} (tutte ammissibili)")
    for i, (r, d, l) in enumerate(zip(b["routes"], b["distances_km"], b["loads_kg"]), 1):
        print(f"  Veicolo {i}: {path(r)}")
        print(f"             distanza {d:.2f} km, carico iniziale {l:g} / {b['capacity_kg']:g} kg")
        print_schedule(b["schedules"][i - 1], n)
    print(f"  Distanza totale:               {b['distance_km']:.2f} km")
    print(f"  Differenza distanze B vs A:    {dist['diff_km']:+.2f} km ({dist['pct_diff_vs_a']:+.2f} %)")

    print("\nCONFRONTO ECONOMICO")
    print(f"  Costo Scenario A:              {comp['cost_a']:.2f} EUR")
    print(f"  Costo Scenario B:              {comp['cost_b']:.2f} EUR")
    print(f"  Differenza assoluta:           {comp['abs_diff']:.2f} EUR")
    print(f"  Differenza % (B vs A):         {comp['pct_diff_vs_a']:+.2f} %")
    print(f"  Scenario piu conveniente:      {comp['cheaper']}")

    print("\nANALISI DI SENSIBILITA")
    for s in results["sensitivity"]:
        be = s["breakeven"]
        if be is None:
            note = "nessun pareggio (differenza indipendente dal parametro)"
        elif s["breakeven_in_range"]:
            note = f"pareggio a {be:.3f} (nell'intervallo)"
        else:
            note = f"nessun pareggio nell'intervallo (retta incrocia a {be:.3f})"
        print(f"  {s['label']}: {note}")
    print()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pianificazione consegne SiciliaFresh")
    parser.add_argument("--no-open", action="store_true", help="non aprire la pagina HTML nel browser")
    args = parser.parse_args(argv)
    # Su Windows l'output rediretto su file usa cp1252: i caratteri non rappresentabili
    # (es. "≤") vengono sostituiti invece di interrompere il programma.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    try:
        instance, results = run()
    except (DataError, InfeasibleInstanceError, VerificationError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1
    print_summary(instance, results)
    page = OUTPUT_DIR / "index.html"
    print(f"Risultati salvati in {OUTPUT_DIR / 'results.json'}")
    print(f"Pagina HTML generata: {page}")
    if not args.no_open:
        webbrowser.open(page.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
