"""Controllo indipendente della matrice delle distanze con un secondo motore di instradamento.

Uso (richiede connessione internet, NON serve per eseguire main.py):
    python tools/check_distances.py

Interroga il servizio pubblico Valhalla della FOSSGIS (https://valhalla1.openstreetmap.de,
profilo "auto") per tutte le coppie ordinate di data/locations.csv e confronta i valori con
data/distances.csv, che resta la fonte principale (OSRM). Scrive data/distances_check.json.

Valhalla usa anch'esso i dati OpenStreetMap: il controllo e indipendente rispetto al motore
di calcolo e al criterio di scelta del percorso, non rispetto ai dati cartografici.
Le differenze vengono documentate, non usate per modificare la matrice.
"""

import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VALHALLA_URL = "https://valhalla1.openstreetmap.de/sources_to_targets?json={payload}"


def main():
    with open(DATA / "locations.csv", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    with open(DATA / "distances.csv", newline="", encoding="utf-8-sig") as handle:
        main_matrix = {r["from"]: {k: float(v) for k, v in r.items() if k != "from"} for r in csv.DictReader(handle)}
    ids = [r["id"] for r in rows]
    points = [{"lat": float(r["lat"]), "lon": float(r["lon"])} for r in rows]
    payload = json.dumps({"sources": points, "targets": points, "costing": "auto", "units": "kilometers"})
    url = VALHALLA_URL.format(payload=urllib.parse.quote(payload))
    request = urllib.request.Request(url, headers={"User-Agent": "siciliafresh-project/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)

    pairs = []
    for i, row in enumerate(data["sources_to_targets"]):
        for j, cell in enumerate(row):
            if i == j:
                continue
            a, b = ids[i], ids[j]
            check_km = cell.get("distance")
            main_km = main_matrix[a][b]
            pairs.append({"from": a, "to": b, "osrm_km": main_km,
                          "valhalla_km": round(check_km, 2) if check_km is not None else None,
                          "diff_km": round(check_km - main_km, 2) if check_km is not None else None,
                          "diff_pct": round((check_km - main_km) / main_km * 100, 1) if check_km is not None else None})

    missing = [p for p in pairs if p["valhalla_km"] is None]
    diffs = [abs(p["diff_km"]) for p in pairs if p["diff_km"] is not None]
    pcts = [abs(p["diff_pct"]) for p in pairs if p["diff_pct"] is not None]
    summary = {"pairs": len(pairs), "missing": len(missing),
               "mean_abs_diff_km": round(sum(diffs) / len(diffs), 3) if diffs else None,
               "max_abs_diff_km": max(diffs) if diffs else None,
               "max_abs_diff_pct": max(pcts) if pcts else None,
               "within_5_pct": sum(1 for p in pcts if p <= 5)}
    result = {"service": "Valhalla, server pubblico FOSSGIS (valhalla1.openstreetmap.de)",
              "data": "OpenStreetMap contributors (licenza ODbL)", "costing": "auto",
              "retrieved_at": datetime.now().isoformat(timespec="seconds"),
              "note": "Controllo di coerenza: la fonte principale della matrice resta OSRM (distances_source.json).",
              "summary": summary, "pairs": pairs}
    with open(DATA / "distances_check.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=1)

    print(f"Coppie confrontate: {summary['pairs']}, senza risposta: {summary['missing']}")
    print(f"Differenza media {summary['mean_abs_diff_km']} km, massima {summary['max_abs_diff_km']} km "
          f"({summary['max_abs_diff_pct']} %); entro il 5 %: {summary['within_5_pct']} coppie")
    for p in sorted(pairs, key=lambda p: -abs(p["diff_pct"] or 0))[:6]:
        print(f"  {p['from']}->{p['to']}: OSRM {p['osrm_km']} km, Valhalla {p['valhalla_km']} km ({p['diff_pct']:+} %)")


if __name__ == "__main__":
    main()
