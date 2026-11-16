"""Caricamento e validazione dei dati di input (CSV e JSON).

Ogni errore nei dati genera una DataError con un messaggio comprensibile,
in modo che il programma si interrompa prima di calcolare risultati privi di senso.
"""

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path


class DataError(ValueError):
    """Dati mancanti, malformati o incoerenti."""


@dataclass
class Instance:
    """Istanza completa del problema: luoghi, domanda, distanze e capacita."""

    depot: str
    clients: list                 # id dei clienti, nell'ordine del file
    names: dict                   # id -> nome della localita
    coords: dict                  # id -> (x, y) schematiche facoltative, solo per il disegno
    demand: dict                  # id cliente -> kg richiesti
    dist: dict                    # (da, a) -> km
    capacity_a: float             # capacita del veicolo dello Scenario A
    capacity_b: float             # capacita di ciascun veicolo dello Scenario B
    config: dict = field(default_factory=dict)
    geo: dict = field(default_factory=dict)        # id -> (lat, lon) reali, se presenti nel CSV
    ref_points: dict = field(default_factory=dict)  # id -> descrizione del punto di riferimento


def _to_number(value, what):
    """Converte una stringa in float positivo o nullo, altrimenti DataError."""
    if value is None or str(value).strip() == "":
        raise DataError(f"Valore mancante: {what}")
    try:
        number = float(str(value).strip().replace(",", "."))
    except ValueError:
        raise DataError(f"Valore non numerico per {what}: '{value}'") from None
    if number != number or number in (float("inf"), float("-inf")):
        raise DataError(f"Valore non valido per {what}: '{value}'")
    if number < 0:
        raise DataError(f"Valore negativo non ammesso per {what}: {number}")
    return number


def _read_csv(path):
    path = Path(path)
    if not path.exists():
        raise DataError(f"File non trovato: {path}")
    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise DataError(f"File vuoto: {path}")
    return rows


def load_json(path):
    path = Path(path)
    if not path.exists():
        raise DataError(f"File non trovato: {path}")
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise DataError(f"JSON non valido in {path}: {exc}") from None


def load_locations(path):
    """Restituisce (depot, clients, names, coords) da locations.csv."""
    depot, clients, names, coords = None, [], {}, {}
    for row in _read_csv(path):
        loc_id = (row.get("id") or "").strip()
        if not loc_id:
            raise DataError("locations.csv: riga senza id")
        if loc_id in names:
            raise DataError(f"locations.csv: id duplicato '{loc_id}'")
        role = (row.get("role") or "").strip().lower()
        names[loc_id] = (row.get("name") or "").strip() or loc_id
        # Coordinate x, y facoltative: se mancano, il disegno usa lat/lon (vedi visualization.schematic_layout)
        if (row.get("x") or "").strip() and (row.get("y") or "").strip():
            coords[loc_id] = (_to_number(row.get("x"), f"x di {loc_id}"),
                              _to_number(row.get("y"), f"y di {loc_id}"))
        if role == "deposito":
            if depot is not None:
                raise DataError("locations.csv: e ammesso un solo deposito")
            depot = loc_id
        elif role == "cliente":
            clients.append(loc_id)
        else:
            raise DataError(f"locations.csv: ruolo sconosciuto '{role}' per {loc_id}")
    if depot is None:
        raise DataError("locations.csv: manca il deposito")
    if not clients:
        raise DataError("locations.csv: nessun cliente definito")
    return depot, clients, names, coords


def load_distances(path, ids):
    """Legge la matrice completa delle distanze e ne verifica la coerenza."""
    rows = _read_csv(path)
    header = [h.strip() for h in rows[0].keys() if h and h.strip() != "from"]
    if set(header) != set(ids):
        raise DataError(f"distances.csv: colonne {sorted(header)} diverse dalle localita {sorted(ids)}")
    dist, seen = {}, set()
    for row in rows:
        origin = (row.get("from") or "").strip()
        if origin not in ids:
            raise DataError(f"distances.csv: localita di partenza sconosciuta '{origin}'")
        if origin in seen:
            raise DataError(f"distances.csv: riga duplicata per '{origin}'")
        seen.add(origin)
        for dest in ids:
            km = _to_number(row.get(dest), f"distanza {origin}->{dest}")
            if origin == dest and km != 0:
                raise DataError(f"distances.csv: la diagonale deve essere 0 ({origin})")
            if origin != dest and km == 0:
                raise DataError(f"distances.csv: distanza nulla tra localita diverse {origin}->{dest}")
            dist[(origin, dest)] = km
    if seen != set(ids):
        raise DataError(f"distances.csv: righe mancanti per {sorted(set(ids) - seen)}")
    return dist


def load_deliveries(path, clients):
    """Legge le quantita richieste (kg) per ogni cliente."""
    demand = {}
    for row in _read_csv(path):
        client = (row.get("id") or "").strip()
        if client not in clients:
            raise DataError(f"deliveries.csv: cliente sconosciuto '{client}'")
        if client in demand:
            raise DataError(f"deliveries.csv: cliente ripetuto '{client}'")
        kg = _to_number(row.get("demand_kg"), f"domanda di {client}")
        if kg == 0:
            raise DataError(f"deliveries.csv: domanda nulla per {client}")
        demand[client] = kg
    missing = [c for c in clients if c not in demand]
    if missing:
        raise DataError(f"deliveries.csv: domanda mancante per {missing}")
    return demand


def load_geo(path):
    """Coordinate reali e punti di riferimento (colonne facoltative di locations.csv)."""
    geo, refs = {}, {}
    for row in _read_csv(path):
        loc_id = (row.get("id") or "").strip()
        if (row.get("lat") or "").strip() and (row.get("lon") or "").strip():
            geo[loc_id] = (float(row["lat"]), float(row["lon"]))
        if (row.get("ref_point") or "").strip():
            refs[loc_id] = row["ref_point"].strip()
    return geo, refs


def load_instance(data_dir):
    """Carica l'intera istanza dalla cartella dei dati."""
    data_dir = Path(data_dir)
    depot, clients, names, coords = load_locations(data_dir / "locations.csv")
    geo, refs = load_geo(data_dir / "locations.csv")
    dist = load_distances(data_dir / "distances.csv", [depot] + clients)
    demand = load_deliveries(data_dir / "deliveries.csv", clients)
    config = load_json(data_dir / "config.json")
    try:
        cap_a = _to_number(config["vehicles"]["scenario_A"]["capacity_kg"], "capacita Scenario A")
        cap_b = _to_number(config["vehicles"]["scenario_B"]["capacity_kg"], "capacita Scenario B")
    except KeyError as exc:
        raise DataError(f"config.json: chiave mancante {exc}") from None
    return Instance(depot, clients, names, coords, demand, dist, cap_a, cap_b, config, geo, refs)
