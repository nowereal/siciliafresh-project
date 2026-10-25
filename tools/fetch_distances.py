"""Recupera la matrice delle distanze stradali da OSRM (dati OpenStreetMap).

Uso (richiede connessione internet, NON serve per eseguire main.py):
    python tools/fetch_distances.py

Legge le coordinate (lat, lon) da data/locations.csv, interroga il servizio
pubblico OSRM (https://router.project-osrm.org, profilo "driving") e scrive:
  - data/distances.csv         matrice direzionale completa in km (2 decimali)
  - data/distances_source.json richiesta, data di rilevazione, risposta grezza e,
                               per ogni coppia, le strade percorse (km per strada)

La matrice NON viene resa simmetrica: la distanza A->B puo differire da B->A
(sensi unici, svincoli, rampe). OSRM restituisce la lunghezza del percorso piu
rapido in auto secondo il proprio modello, non del percorso piu corto.
"""

import csv
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OSRM_URL = "https://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance,duration"
ROUTE_URL = "https://router.project-osrm.org/route/v1/driving/{coords}?overview=false&steps=true"


def route_roads(a, b):
    """Strade principali (km per strada) del percorso OSRM da a verso b."""
    coords = f"{float(a['lon']):.7f},{float(a['lat']):.7f};{float(b['lon']):.7f},{float(b['lat']):.7f}"
    request = urllib.request.Request(ROUTE_URL.format(coords=coords),
                                     headers={"User-Agent": "siciliafresh-project/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    roads = {}
    for step in data["routes"][0]["legs"][0]["steps"]:
        name = step.get("ref") or step.get("name") or "(senza nome)"
        roads[name] = roads.get(name, 0) + step["distance"] / 1000
    main_roads = sorted(roads.items(), key=lambda item: -item[1])
    return {"distance_km": round(data["routes"][0]["distance"] / 1000, 2),
            "roads_km": [[name, round(km, 2)] for name, km in main_roads if km >= 0.2]}


def main():
    with open(DATA / "locations.csv", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    ids = [r["id"] for r in rows]
    coords = ";".join(f"{float(r['lon']):.7f},{float(r['lat']):.7f}" for r in rows)
    url = OSRM_URL.format(coords=coords)
    request = urllib.request.Request(url, headers={"User-Agent": "siciliafresh-project/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("code") != "Ok":
        raise SystemExit(f"Risposta OSRM non valida: {data.get('code')} {data.get('message', '')}")

    with open(DATA / "distances.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["from"] + ids)
        for origin, row in zip(ids, data["distances"]):
            writer.writerow([origin] + [f"{meters / 1000:.2f}" for meters in row])

    # Per ogni coppia ordinata registra le strade percorse, per poter controllare
    # che i collegamenti usino la viabilita costiera ordinaria e non strade montane.
    routes = {}
    for i, a in enumerate(rows):
        for j, b in enumerate(rows):
            if i != j:
                routes[f"{ids[i]}->{ids[j]}"] = route_roads(a, b)
                time.sleep(0.3)  # uso rispettoso del server pubblico

    source = {
        "service": "OSRM - Open Source Routing Machine, server dimostrativo pubblico",
        "data": "OpenStreetMap contributors (licenza ODbL)",
        "profile": "driving (auto), percorso piu rapido secondo il modello OSRM",
        "retrieved_at": datetime.now().isoformat(timespec="seconds"),
        "request_url": url,
        "ids": ids,
        "response": data,
        "routes": routes,
    }
    with open(DATA / "distances_source.json", "w", encoding="utf-8") as handle:
        json.dump(source, handle, ensure_ascii=False, indent=1)

    print(f"Scritta la matrice {len(ids)}x{len(ids)} in data/distances.csv")
    for s, i in zip(data["sources"], ids):
        print(f"  {i}: agganciato a '{s['name']}' a {s['distance']:.1f} m dal punto di riferimento")
    print("Strade principali per coppia (km):")
    for pair, info in routes.items():
        roads = ", ".join(f"{name} {km:g}" for name, km in info["roads_km"][:4])
        print(f"  {pair}: {info['distance_km']} km - {roads}")


if __name__ == "__main__":
    main()
