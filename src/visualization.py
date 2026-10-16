"""Generazione della pagina HTML a partire dai risultati calcolati.

La pagina e statica: Python scrive nell'HTML tutti i numeri, i percorsi, i grafi
e i grafici (SVG). Il file output/app.js aggiunge soltanto interazioni e
animazioni (selettore degli scenari, tooltip, comparsa delle sezioni): senza
JavaScript, o con le animazioni ridotte, la pagina mostra comunque tutti i dati.

I valori principali sono marcati con l'attributo data-key, cosi i test possono
confrontarli automaticamente con output/results.json.
"""

import json
import math
from html import escape

# Colori dei veicoli (tinta = veicolo): stessi valori delle variabili CSS --v1 e --v2 in styles.css.
# Coppia validata per contrasto e per le principali forme di daltonismo.
VEHICLE_COLORS = ("#C85B2A", "#287B91")
# Colori degli scenari nei grafici economici (tono del marchio = scenario): --sa e --sb.
COLOR_A = "#174F46"     # Scenario A, verde petrolio scuro
COLOR_B = "#7C9D93"     # Scenario B, salvia scuro (stessa tinta, piu chiaro)
COMPONENTS = (("fixed", "Costo fisso"), ("driver", "Autista"),
              ("fuel", "Carburante"), ("other_km", "Altri costi al km"))


# ---------------------------------------------------------------------------
# Formattazione
# ---------------------------------------------------------------------------

def num(value, decimals=2):
    """Numero in formato italiano: 1.234,56"""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def eur(value):
    return f"{num(value)}&nbsp;€"


def km(value):
    return f"{num(value, 2)}&nbsp;km"


def num_param(value):
    """Valore di un parametro: tre decimali solo se servono (es. 2,265 €/l), altrimenti due."""
    return num(value, 3 if abs(value * 100 - round(value * 100)) > 1e-9 else 2)


def signed_pct(value):
    return ("+" if value > 0 else "") + num(value) + "&nbsp;%"


def tagged(key, text):
    """Valore marcato per la verifica automatica HTML <-> results.json."""
    return f'<span data-key="{escape(key)}">{text}</span>'


def counter(value, decimals, text=None):
    """Numero che app.js puo animare da zero; il testo iniziale e gia il valore finale."""
    return (f'<span class="count" data-count="{value:.6f}" data-decimals="{decimals}">'
            f'{text if text is not None else num(value, decimals)}</span>')


def nice_ticks(lo, hi, count=5):
    raw = (hi - lo) / count if hi > lo else 1
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), default=raw)
    start = math.floor(lo / step) * step
    ticks, v = [], start
    while v <= hi + step * 0.001:
        ticks.append(round(v, 10))
        v += step
    if ticks[-1] < hi:
        ticks.append(round(ticks[-1] + step, 10))
    return ticks


def section_head(number, eyebrow, title, intro=""):
    intro_html = f'<p class="section-intro">{intro}</p>' if intro else ""
    return (f'<header class="section-head reveal"><p class="eyebrow"><span>{number}</span>{eyebrow}</p>'
            f'<h2>{title}</h2>{intro_html}</header>')


# ---------------------------------------------------------------------------
# Hero: la costa come linea, con le fermate alla longitudine reale
# ---------------------------------------------------------------------------

def coast_strip(instance):
    """Striscia ovest-est: posizione proporzionale alla longitudine reale, barre = kg richiesti."""
    ids = [instance.depot] + instance.clients
    if not all(i in instance.geo for i in ids):
        return ""
    width, height, pad_l, pad_r, base = 1040, 236, 44, 44, 132
    lons = [instance.geo[i][1] for i in ids]
    lo, hi = min(lons), max(lons)
    km_per_deg = 111.32 * math.cos(math.radians(sum(instance.geo[i][0] for i in ids) / len(ids)))
    span_km = (hi - lo) * km_per_deg
    scale = (width - pad_l - pad_r) / ((hi - lo) or 1)

    def x_of(loc):
        return pad_l + (instance.geo[loc][1] - lo) * scale

    max_kg = max(instance.demand.values())
    parts = [f'<svg class="coast" viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="Località disposte da ovest a est secondo la longitudine reale, con la quantità richiesta">',
             f'<line x1="{pad_l}" y1="{base}" x2="{width - pad_r}" y2="{base}" class="coast-line"/>']

    # Etichette su due righe quando le localita sono troppo vicine
    order = sorted(ids, key=x_of)
    rows_last = [-1e9, -1e9]
    label_row = {}
    for loc in order:
        x = x_of(loc)
        row = 0 if x - rows_last[0] > 150 else 1
        label_row[loc] = row
        rows_last[row] = x

    for loc in order:
        x = x_of(loc)
        name = escape(instance.names[loc])
        y_label = base + 34 + label_row[loc] * 40
        parts.append(f'<line x1="{x:.1f}" y1="{base + 8}" x2="{x:.1f}" y2="{y_label - 14}" class="coast-leader"/>')
        if loc == instance.depot:
            parts.append(f'<rect x="{x - 7:.1f}" y="{base - 7}" width="14" height="14" rx="3" class="coast-depot"/>')
            parts.append(f'<text x="{x:.1f}" y="{y_label}" class="coast-name" text-anchor="middle">{name}</text>'
                         f'<text x="{x:.1f}" y="{y_label + 16}" class="coast-sub" text-anchor="middle">deposito</text>')
        else:
            kg = instance.demand[loc]
            h = 82 * kg / max_kg
            parts.append(f'<path d="M{x - 6:.1f},{base - 6} v{-(h - 4):.1f} a4,4 0 0 1 4,-4 h4 a4,4 0 0 1 4,4 '
                         f'v{h - 4:.1f} z" class="coast-bar" data-tip="{name}: {num(kg, 0)} kg richiesti"/>')
            parts.append(f'<text x="{x:.1f}" y="{base - h - 14:.1f}" class="coast-kg" text-anchor="middle">'
                         f'{num(kg, 0)}</text>')
            parts.append(f'<circle cx="{x:.1f}" cy="{base}" r="4.5" class="coast-stop"/>')
            parts.append(f'<text x="{x:.1f}" y="{y_label}" class="coast-name" text-anchor="middle">{name}</text>'
                         f'<text x="{x:.1f}" y="{y_label + 16}" class="coast-sub" text-anchor="middle">cliente</text>')

    # Barra di scala (valida in direzione est-ovest, perche x e proporzionale alla longitudine)
    bar_km = 2
    bar_px = bar_km / span_km * (width - pad_l - pad_r)
    sx = pad_l + (width - pad_l - pad_r) * 0.24   # zona centrale libera tra Milazzo e il deposito
    parts.append(f'<g class="coast-scale"><line x1="{sx:.1f}" y1="70" x2="{sx + bar_px:.1f}" y2="70"/>'
                 f'<line x1="{sx:.1f}" y1="65" x2="{sx:.1f}" y2="75"/>'
                 f'<line x1="{sx + bar_px:.1f}" y1="65" x2="{sx + bar_px:.1f}" y2="75"/>'
                 f'<text x="{sx:.1f}" y="56">{bar_km} km in linea d\'aria (ovest–est)</text></g>')
    parts.append(f'<text x="{sx:.1f}" y="104" class="coast-sub">barre: kg richiesti</text>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Route Explorer: grafo schematico di uno scenario
# ---------------------------------------------------------------------------

def _quad(p0, c, p1, t):
    """Punto e tangente di una curva di Bezier quadratica."""
    u = 1 - t
    x = u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0]
    y = u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1]
    tx = 2 * u * (c[0] - p0[0]) + 2 * t * (p1[0] - c[0])
    ty = 2 * u * (c[1] - p0[1]) + 2 * t * (p1[1] - c[1])
    return x, y, tx, ty


def schematic_layout(instance, rank_weight=0.5, gamma=0.8):
    """Posizioni schematiche dei nodi (0..1), uguali in tutti i grafi.

    Se il CSV fornisce lat/lon: l'ascissa segue l'ordine ovest-est e la verticale
    l'ordine nord-sud. Per l'ascissa si fa una media tra la longitudine normalizzata
    e la posizione in classifica ovest-est: la trasformazione non e proporzionale
    (allarga il gruppo di localita vicine a est del deposito) ma conserva l'ordine
    geografico. Per la verticale (nord in alto) la latitudine normalizzata e elevata
    a gamma < 1: la trasformazione e monotona, quindi l'ordine nord-sud non cambia,
    ma separa meglio i nodi della fascia costiera dagli archi che li sfiorano.
    Le distanze mostrate nel grafo provengono sempre dalla matrice stradale.
    Senza lat/lon si usano le colonne x, y del CSV.
    """
    ids = [instance.depot] + instance.clients
    if all(i in instance.geo for i in ids):
        lats = {i: instance.geo[i][0] for i in ids}
        lons = {i: instance.geo[i][1] for i in ids}
        order = sorted(ids, key=lambda i: lons[i])
        lo, hi = min(lons.values()), max(lons.values())
        la_lo, la_hi = min(lats.values()), max(lats.values())
        layout = {}
        for rank, i in enumerate(order):
            x = rank_weight * rank / (len(ids) - 1) + (1 - rank_weight) * (lons[i] - lo) / ((hi - lo) or 1)
            y = ((la_hi - lats[i]) / ((la_hi - la_lo) or 1)) ** gamma
            layout[i] = (x, y)
        return layout
    xs = [instance.coords[i][0] for i in ids]
    ys = [instance.coords[i][1] for i in ids]
    return {i: ((instance.coords[i][0] - min(xs)) / ((max(xs) - min(xs)) or 1),
                (instance.coords[i][1] - min(ys)) / ((max(ys) - min(ys)) or 1)) for i in ids}


def route_graph(instance, key, results, title):
    """Grafo SVG dei percorsi di uno scenario su posizioni schematiche.

    Ogni veicolo ha il proprio colore (variabili CSS --v1, --v2) e linee continue.
    Gli archi sono leggermente curvi verso la destra del senso di marcia: due archi
    tra gli stessi nodi in versi opposti, o paralleli, restano cosi distinguibili.
    """
    width, height, pad = 760, 470, 70
    layout = schematic_layout(instance)

    def pos(loc):
        x, y = layout[loc]
        return (pad + x * (width - 2 * pad), pad + y * (height - 2 * pad))

    if key == "A":
        routes, schedules = [results["scenario_A"]["route"]], [results["scenario_A"]["schedule"]]
    else:
        routes, schedules = results["scenario_B"]["routes"], results["scenario_B"]["schedules"]
    multi = len(routes) > 1

    # Ordine di visita e carico residuo dopo la consegna, per ogni cliente
    visit = {}
    for v, sched in enumerate(schedules):
        for k, step in enumerate(sched["steps"][1:-1], 1):
            visit[step["stop"]] = (v, k, step["delivered_kg"], step["residual_kg"])

    # Geometria degli archi (curve) e punti campionati per evitare sovrapposizioni
    all_nodes = [instance.depot] + instance.clients
    pairs = {(a, b) for route in routes for a, b in zip(route, route[1:])}

    def clearance(p0, c, p1, others):
        """Distanza minima tra la curva e i centri dei nodi che l'arco non collega."""
        pts = [_quad(p0, c, p1, s / 30)[:2] for s in range(1, 30)]
        return min((math.hypot(px_ - ox, py_ - oy) for px_, py_ in pts for ox, oy in others), default=1e9)

    edges = []
    for v, route in enumerate(routes):
        for a, b in zip(route, route[1:]):
            p0, p1 = pos(a), pos(b)
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            length = math.hypot(dx, dy) or 1
            nx, ny = -dy / length, dx / length          # normale a destra del senso di marcia (y verso il basso)
            mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            others = [pos(o) for o in all_nodes if o not in (a, b)]
            # Curvatura lieve verso destra; se l'arco sfiora un altro nodo si prova il lato opposto
            # o una curvatura un po' maggiore (al massimo il 22% della corda). Se esiste anche
            # l'arco inverso, si resta a destra, cosi i due versi restano separati.
            sides = (1,) if (b, a) in pairs else (1, -1)
            options = [(side, min(f * length, cap)) for f, cap in ((0.11, 30), (0.16, 42), (0.22, 55)) for side in sides]
            best = None
            for side, bend in options:
                c = (mid[0] + nx * bend * side, mid[1] + ny * bend * side)
                gap = clearance(p0, c, p1, others)
                if gap >= 34:
                    best = (side, c)
                    break
                if best is None or gap > best[2]:
                    best = (side, c, gap)
            side, c = best[0], best[1]
            edges.append({"v": v, "a": a, "b": b, "p0": p0, "p1": p1, "c": c, "n": (nx * side, ny * side)})
    curve_pts = [_quad(e["p0"], e["c"], e["p1"], s / 40)[:2] for e in edges for s in range(41)]

    def score(box, boxes):
        bx, by, bw, bh = box
        on_lines = sum(1 for px_, py_ in curve_pts if bx <= px_ <= bx + bw and by <= py_ <= by + bh)
        over = sum(1 for ox, oy, ow, oh in boxes if bx < ox + ow and ox < bx + bw and by < oy + oh and oy < by + bh)
        outside = 0 if (0 <= bx and bx + bw <= width and 0 <= by and by + bh <= height) else 50
        return on_lines + 20 * over + outside

    obstacles = [(pos(l)[0] - 19, pos(l)[1] - 19, 38, 38) for l in [instance.depot] + instance.clients]

    # Frecce di direzione a meta arco (diventano ostacoli per le etichette)
    arrows = []
    for e in edges:
        x, y, tx, ty = _quad(e["p0"], e["c"], e["p1"], 0.5)
        ang = math.degrees(math.atan2(ty, tx))
        arrows.append(f'<path d="M-6,-5.5 L5,0 L-6,5.5" class="g-chev" style="--vc:var(--v{e["v"] + 1})" '
                      f'transform="translate({x:.1f},{y:.1f}) rotate({ang:.1f})"/>')
        obstacles.append((x - 9, y - 9, 18, 18))

    # Etichette dei nodi: nome e consegna, nella posizione con meno conflitti
    node_parts = []
    for loc in [instance.depot] + instance.clients:
        x, y = pos(loc)
        name = instance.names[loc]
        if loc == instance.depot:
            sub = "deposito · partenza e rientro"
        else:
            sub = f"consegna {num(instance.demand[loc], 0)} kg"
        text_w = max(7.4 * len(name), 6.4 * len(sub))
        options = [("start", 24, -1, (x + 20, y - 16, text_w + 8, 38)),
                   ("end", -24, -1, (x - 28 - text_w, y - 16, text_w + 8, 38)),
                   ("middle", 0, -44, (x - text_w / 2 - 4, y - 60, text_w + 8, 38)),
                   ("middle", 0, 36, (x - text_w / 2 - 4, y + 20, text_w + 8, 38)),
                   ("start", 16, -34, (x + 12, y - 50, text_w + 8, 38)),      # in alto a destra
                   ("end", -16, -34, (x - 20 - text_w, y - 50, text_w + 8, 38)),  # in alto a sinistra
                   ("start", 16, 30, (x + 12, y + 14, text_w + 8, 38)),       # in basso a destra
                   ("end", -16, 30, (x - 20 - text_w, y + 14, text_w + 8, 38)),   # in basso a sinistra
                   # posizioni un poco piu distanti, usate solo se le precedenti sono occupate
                   ("start", 26, 18, (x + 22, y + 2, text_w + 8, 38)),
                   ("end", -26, 18, (x - 30 - text_w, y + 2, text_w + 8, 38)),
                   ("start", 26, -20, (x + 22, y - 36, text_w + 8, 38)),
                   ("end", -26, -20, (x - 30 - text_w, y - 36, text_w + 8, 38)),
                   ("middle", 0, 52, (x - text_w / 2 - 4, y + 36, text_w + 8, 38)),
                   ("middle", 0, -60, (x - text_w / 2 - 4, y - 76, text_w + 8, 38))]
        anchor, dx, dy, box = min(options, key=lambda o: score(o[3], obstacles))
        obstacles.append(box)
        if loc == instance.depot:
            parts_dep = "; ".join(
                f"veicolo {v + 1} parte con {num(s['initial_load_kg'], 0)} kg" if multi else
                f"partenza con {num(s['initial_load_kg'], 0)} kg"
                for v, s in enumerate(schedules))
            tip = f"{escape(name)} — deposito. {parts_dep[:1].upper() + parts_dep[1:]}; rientro a vuoto (0 kg)."
            node = (f'<rect x="{x - 16:.1f}" y="{y - 16:.1f}" width="32" height="32" rx="8" class="g-depot"/>'
                    f'<path d="M{x - 8:.1f},{y + 1:.1f} L{x:.1f},{y - 6:.1f} L{x + 8:.1f},{y + 1:.1f} '
                    f'V{y + 8:.1f} H{x - 8:.1f} Z" class="g-depot-icon"/>')
        else:
            v, k, delivered, residual = visit[loc]
            tip = (f"Veicolo {v + 1} · fermata {k} · {escape(name)}: consegna {num(delivered, 0)} kg; "
                   f"carico residuo dopo la consegna {num(residual, 0)} kg")
            node = (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" class="g-stop" style="--vc:var(--v{v + 1})"/>'
                    f'<text x="{x:.1f}" y="{y + 4.8:.1f}" class="g-order" text-anchor="middle">{k}</text>')
        node_parts.append(f'<g class="g-node" data-tip="{tip}" tabindex="0">{node}'
                          f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" class="g-name" text-anchor="{anchor}">{escape(name)}</text>'
                          f'<text x="{x + dx:.1f}" y="{y + dy + 16:.1f}" class="g-sub" text-anchor="{anchor}">{sub}</text></g>')

    # Etichette dei km: sul lato esterno della curva, nel punto libero piu vicino al centro
    labels = []
    for e in edges:
        text = num(instance.dist[(e["a"], e["b"])], 2)
        w = 10 + 7.2 * len(text)
        best = None
        # Prima vicino all'arco (17 px); sugli archi molto corti, se serve, un poco piu distante (28 px)
        for offset in (17, 28):
            for t in (0.5, 0.38, 0.62, 0.28, 0.72):
                for side in (1, -1):
                    x, y, _, _ = _quad(e["p0"], e["c"], e["p1"], t)
                    mx, my = x + e["n"][0] * offset * side, y + e["n"][1] * offset * side
                    box = (mx - w / 2 - 2, my - 12, w + 4, 24)      # con un piccolo margine
                    s = score(box, obstacles)
                    if best is None or s < best[0]:
                        best = (s, mx, my, box)
                if best[0] == 0:
                    break
            if best[0] == 0:
                break
        _, mx, my, box = best
        obstacles.append(box)
        labels.append(f'<g class="g-leg" data-tip="Veicolo {e["v"] + 1}: {escape(instance.names[e["a"]])} → '
                      f'{escape(instance.names[e["b"]])}, {text} km">'
                      f'<rect x="{mx - w / 2:.1f}" y="{my - 10:.1f}" width="{w:.1f}" height="20" rx="10" '
                      f'style="--vc:var(--v{e["v"] + 1})"/>'
                      f'<text x="{mx:.1f}" y="{my + 4:.1f}" text-anchor="middle">{text}</text></g>')

    defs, paths = [], []
    for v, route in enumerate(routes):
        segs = [e for e in edges if e["v"] == v]
        d = f'M{segs[0]["p0"][0]:.1f},{segs[0]["p0"][1]:.1f}' + "".join(
            f' Q{e["c"][0]:.1f},{e["c"][1]:.1f} {e["p1"][0]:.1f},{e["p1"][1]:.1f}' for e in segs)
        mid = f"mask-{key}-{v}"
        defs.append(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{width}" height="{height}">'
                    f'<path d="{d}" class="g-draw" data-delay="{v * 450}"/></mask>')
        paths.append(f'<path d="{d}" class="g-route" style="--vc:var(--v{v + 1})" mask="url(#{mid})"/>')

    return (f'<svg class="graph" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
            f'<defs>{"".join(defs)}</defs>{"".join(paths)}{"".join(arrows)}{"".join(labels)}'
            f'{"".join(node_parts)}</svg>')


def delivery_timeline(instance, schedule, v):
    """Sequenza delle consegne di un veicolo: consegna, carico residuo e km di ogni tratto."""
    cap = schedule["capacity_kg"]
    rows = []
    for k, step in enumerate(schedule["steps"]):
        name = escape(instance.names[step["stop"]])
        share = step["residual_kg"] / cap * 100
        bar = (f'<span class="tl-bar" role="img" aria-label="Carico residuo {num(step["residual_kg"], 0)} kg">'
               f'<span style="--w:{share:.1f}%"></span></span>')
        if step["kind"] == "partenza":
            rows.append(f'<li class="tl-row tl-start"><span class="tl-dot d">D</span>'
                        f'<span class="tl-main"><b>{name}</b><small>Partenza dal deposito</small></span>'
                        f'<span class="tl-load">{bar}<span>Carico iniziale <b>{num(step["residual_kg"], 0)}&nbsp;kg</b></span></span>'
                        f'<span class="tl-km"></span></li>')
        elif step["kind"] == "consegna":
            rows.append(f'<li class="tl-row"><span class="tl-dot">{k}</span>'
                        f'<span class="tl-main"><b>{name}</b><small>Consegna <b>{num(step["delivered_kg"], 0)}&nbsp;kg</b></small></span>'
                        f'<span class="tl-load">{bar}<span>Residuo <b>{num(step["residual_kg"], 0)}&nbsp;kg</b></span></span>'
                        f'<span class="tl-km">+{num(step["leg_km"], 2)}&nbsp;km</span></li>')
        else:
            rows.append(f'<li class="tl-row tl-end"><span class="tl-dot d">D</span>'
                        f'<span class="tl-main"><b>{name}</b><small>Rientro a vuoto</small></span>'
                        f'<span class="tl-load">{bar}<span>Residuo <b>0&nbsp;kg</b></span></span>'
                        f'<span class="tl-km">+{num(step["leg_km"], 2)}&nbsp;km<em>{num(step["cumulative_km"], 2)}&nbsp;km in totale</em></span></li>')
    return f'<ol class="timeline" style="--vc:var(--v{v + 1})">{"".join(rows)}</ol>'


def vehicle_block(instance, index, schedule, dist_km, cost, keys, single):
    cap = schedule["capacity_kg"]
    load = schedule["initial_load_kg"]
    pct = load / cap * 100
    title = "Veicolo unico" if single else f"Veicolo {index}"
    return f"""
      <div class="vehicle" style="--vc:var(--v{index})">
        <div class="vehicle-head"><span class="v-swatch" aria-hidden="true"></span><h4>{title}</h4>
          <span class="vehicle-meta">{tagged(keys['distance'], km(dist_km))} · {tagged(keys['cost'], eur(cost['total']))} · {num(cost['hours'], 2)}&nbsp;h</span></div>
        <div class="meter" role="img" aria-label="Carico iniziale {num(load, 0)} kg su una capacità di {num(cap, 0)} kg">
          <span style="--w:{pct:.1f}%"></span></div>
        <p class="meter-label">Carico iniziale <b>{tagged(keys['load'], num(load, 0))}&nbsp;kg</b> su {num(cap, 0)} kg di capacità
          <span>{num(pct, 0)}&nbsp;%</span></p>
        {delivery_timeline(instance, schedule, index - 1)}
      </div>"""


def scenario_panel(instance, results, key):
    costs = results["costs"][key]
    if key == "A":
        a = results["scenario_A"]
        schedules, dists = [a["schedule"]], [a["distance_km"]]
        cap, total_km = a["capacity_kg"], a["distance_km"]
        keys = [{"distance": "a.v1.distance_km", "cost": "a.v1.cost_total", "load": "a.load_kg"}]
        title, subtitle = "Scenario A", f"Un furgone da {num(cap, 0)} kg consegna a tutti i clienti in un solo giro"
        enum = (f'<p class="enum"><b>{tagged("a.evaluated", a["evaluated"])}</b> permutazioni '
                f'esaminate ({len(instance.clients)}! = {math.factorial(len(instance.clients))}), tutte ammissibili.</p>')
        total_key, cost_key = "a.distance_km", "a.cost_total"
    else:
        b = results["scenario_B"]
        schedules, dists = b["schedules"], b["distances_km"]
        cap, total_km = b["capacity_kg"], b["distance_km"]
        keys = [{"distance": f"b.v{i}.distance_km", "cost": f"b.v{i}.cost_total", "load": f"b.v{i}.load_kg"}
                for i in (1, 2)]
        title, subtitle = "Scenario B", f"Due furgoni identici da {num(cap, 0)} kg si dividono le consegne"
        enum = (f'<p class="enum"><b>{tagged("b.partitions_examined", b["partitions_examined"])}</b> ripartizioni '
                f'esaminate → <b>{tagged("b.feasible_partitions", b["feasible_partitions"])}</b> rispettano la capacità → '
                f'<b>{tagged("b.evaluated", b["evaluated"])}</b> combinazioni di percorsi valutate.</p>')
        total_key, cost_key = "b.distance_km", "b.cost_total"

    other_key = "B" if key == "A" else "A"
    delta = costs["totals"]["total"] - results["costs"][other_key]["totals"]["total"]
    verdict = "più conveniente" if delta < 0 else ("costo uguale" if delta == 0 else "più costoso")
    vehicles = "".join(
        vehicle_block(instance, i + 1, s, d, costs["vehicles"][i], keys[i], key == "A")
        for i, (s, d) in enumerate(zip(schedules, dists)))
    return f"""
    <div class="panel" data-scenario-panel="{key}">
      <p class="panel-kicker">{title}</p>
      <p class="panel-sub">{subtitle}</p>
      <div class="panel-figures">
        <div><span>Distanza totale</span><b>{tagged(total_key, km(total_km))}</b></div>
        <div><span>Costo giornaliero</span><b>{tagged(cost_key, eur(costs['totals']['total']))}</b></div>
      </div>
      <p class="panel-delta"><b>{('+' if delta > 0 else '−')}{eur(abs(delta))}</b> rispetto allo Scenario {other_key} · {verdict}</p>
      {vehicles}
      {enum}
    </div>"""


def partitions_table(instance, results):
    b = results["scenario_B"]
    rows = []
    for p in sorted(b["partitions"], key=lambda p: (not p["feasible"], p["best_km"] or 0)):
        g1 = ", ".join(escape(instance.names[c]) for c in p["group1"])
        g2 = ", ".join(escape(instance.names[c]) for c in p["group2"])
        best = num(p["best_km"], 2) if p["best_km"] is not None else "—"
        opt = p["best_km"] is not None and abs(p["best_km"] - b["distance_km"]) < 1e-9
        cls = "opt" if opt else ("" if p["feasible"] else "muted")
        rows.append(f"<tr class='{cls}'><td>{g1}</td><td class='n'>{num(p['load1'], 0)}</td><td>{g2}</td>"
                    f"<td class='n'>{num(p['load2'], 0)}</td><td>{'sì' if p['feasible'] else 'no — capacità superata'}</td>"
                    f"<td class='n'>{best}</td></tr>")
    return f"""
    <details class="more">
      <summary>Tutte le {b['partitions_examined']} ripartizioni dello Scenario B</summary>
      <div class="table-wrap"><table>
        <thead><tr><th>Clienti del veicolo 1</th><th class='n'>Carico iniziale (kg)</th><th>Clienti del veicolo 2</th>
        <th class='n'>Carico iniziale (kg)</th><th>Ammissibile</th><th class='n'>Miglior distanza (km)</th></tr></thead>
        <tbody>{''.join(rows)}</tbody></table></div>
      <p class="note">Il carico iniziale di un veicolo è la somma delle quantità da consegnare ai suoi clienti e non può
      superare 900 kg. Il primo cliente è sempre assegnato al veicolo 1: scambiare due veicoli identici non produce una
      soluzione nuova. In evidenza la ripartizione ottimale.</p>
    </details>"""


def graph_legend(key, results):
    if key == "A":
        load = results["scenario_A"]["schedule"]["initial_load_kg"]
        items = [(1, f"Veicolo unico · parte con {num(load, 0)} kg")]
    else:
        items = [(i + 1, f"Veicolo {i + 1} · parte con {num(s['initial_load_kg'], 0)} kg")
                 for i, s in enumerate(results["scenario_B"]["schedules"])]
    spans = "".join(f'<span><i class="v-line" style="--vc:var(--v{v})"></i>{label}</span>' for v, label in items)
    return (f'<div class="legend">{spans}<span><i class="d-key"></i>Deposito</span>'
            f'<span><i class="n-key">1</i>Ordine di consegna</span></div>')


def section_explorer(instance, results):
    graph_a = route_graph(instance, "A", results, "Percorso ottimale, Scenario A")
    graph_b = route_graph(instance, "B", results, "Percorsi ottimali dei due veicoli, Scenario B")
    return f"""
<section id="percorsi" class="section">
  {section_head("02", "Route Explorer", "I percorsi ottimali e le consegne",
                "Ogni veicolo parte dal deposito con la merce dei clienti che gli sono assegnati, consegna a ciascuno "
                "la quantità richiesta e rientra vuoto. L'ordine di visita è quello di lunghezza minima trovato "
                "dall'algoritmo. Seleziona uno scenario per confrontare percorsi, consegne e costi.")}
  <div class="explorer reveal">
    <div class="switch" role="group" aria-label="Scenario visualizzato">
      <button type="button" data-scenario-btn="A" aria-pressed="true">
        <i style="--vc:var(--v1)"></i><span>Scenario A</span><small>1 veicolo</small></button>
      <button type="button" data-scenario-btn="B" aria-pressed="false">
        <i style="--vc:var(--v1)"></i><i style="--vc:var(--v2)"></i><span>Scenario B</span><small>2 veicoli</small></button>
    </div>
    <div class="explorer-grid">
      <figure class="stage">
        <div class="stage-graph" data-scenario-graph="A"><p class="stage-label">Scenario A</p>{graph_a}{graph_legend("A", results)}</div>
        <div class="stage-graph" data-scenario-graph="B"><p class="stage-label">Scenario B</p>{graph_b}{graph_legend("B", results)}</div>
        <figcaption>Schema non in scala: la posizione dei nodi è indicativa. Le etichette sugli archi riportano i km
        stradali reali del tratto nel verso di percorrenza; le frecce indicano il senso di marcia, i numeri l'ordine
        delle consegne. Passa sui nodi per vedere consegna e carico residuo.</figcaption>
      </figure>
      <div class="panels">{scenario_panel(instance, results, "A")}{scenario_panel(instance, results, "B")}</div>
    </div>
    {partitions_table(instance, results)}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# Dati logistici
# ---------------------------------------------------------------------------

def section_data(instance, results):
    ids = [instance.depot] + instance.clients
    status = instance.config["distance_data"]
    rows = []
    for loc in ids:
        kg = "—" if loc == instance.depot else num(instance.demand[loc], 0)
        role = "Deposito" if loc == instance.depot else "Cliente"
        ref = escape(instance.ref_points.get(loc, ""))
        rows.append(f"<tr><td class='id'>{escape(loc)}</td><td><b>{escape(instance.names[loc])}</b>"
                    f"<small>{ref}</small></td><td>{role}</td><td class='n'>{kg}</td></tr>")
    total = sum(instance.demand.values())
    rows.append(f"<tr class='total'><td></td><td>Domanda totale</td><td></td>"
                f"<td class='n'>{tagged('total_demand_kg', num(total, 0))}</td></tr>")

    off = [instance.dist[(a, b)] for a in ids for b in ids if a != b]
    lo, hi = min(off), max(off)
    head = "".join(f"<th>{escape(i)}</th>" for i in ids)
    matrix = []
    for a in ids:
        cells = []
        for b in ids:
            if a == b:
                cells.append("<td class='diag'>·</td>")
            else:
                d = instance.dist[(a, b)]
                share = 0.08 + 0.55 * (d - lo) / ((hi - lo) or 1)
                cells.append(f"<td style='--s:{share * 100:.0f}%' data-tip='{escape(instance.names[a])} → "
                             f"{escape(instance.names[b])}: {num(d, 2)} km'>{num(d, 2)}</td>")
        matrix.append(f"<tr><th>{escape(a)}</th>{''.join(cells)}</tr>")

    checks = "".join(
        f"<li class='{'ok' if c['passed'] else 'ko'}'><span aria-hidden='true'>{'✓' if c['passed'] else '✕'}</span>"
        f"<div>{escape(c['check'])}<small>{escape(c['detail'])}</small></div></li>"
        for c in results["instance_checks"])
    veh = instance.config["vehicles"]
    return f"""
<section id="dati" class="section">
  {section_head("03", "Dati logistici", "Località, domanda, distanze",
                "Località e distanze stradali sono reali; clienti e quantità sono simulati a scopo didattico.")}
  <div class="data-grid reveal">
    <div>
      <div class="table-wrap"><table class="places">
        <thead><tr><th>ID</th><th>Località e punto di riferimento</th><th>Ruolo</th><th class='n'>Domanda (kg)</th></tr></thead>
        <tbody>{''.join(rows)}</tbody></table></div>
      <dl class="capacity">
        <div><dt>Scenario A</dt><dd>{veh['scenario_A']['count']} × {tagged('capacity_a_kg', num(instance.capacity_a, 0))} kg</dd></div>
        <div><dt>Scenario B</dt><dd>{veh['scenario_B']['count']} × {tagged('capacity_b_kg', num(instance.capacity_b, 0))} kg</dd></div>
      </dl>
    </div>
    <div>
      <p class="mini-title">Matrice delle distanze stradali (km) · riga = partenza, colonna = arrivo</p>
      <div class="table-wrap"><table class="matrix"><thead><tr><th></th>{head}</tr></thead>
        <tbody>{''.join(matrix)}</tbody></table></div>
      <p class="note">{escape(status['source'])}</p>
      <p class="mini-title">Verifiche automatiche dell'istanza</p>
      <ul class="checks">{checks}</ul>
    </div>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# Analisi economica
# ---------------------------------------------------------------------------

def component_chart(costs):
    """Barre affiancate A/B per ciascuna voce di costo (stesso asse, valore in punta)."""
    width, left, right, row_h, top = 640, 150, 70, 58, 8
    max_v = max(costs[k]["totals"][c] for k in "AB" for c, _ in COMPONENTS)
    ticks = nice_ticks(0, max_v, 4)
    scale = (width - left - right) / ticks[-1]
    height = top + row_h * len(COMPONENTS) + 26
    parts = [f'<svg class="chart bars" viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="Confronto delle voci di costo tra Scenario A e Scenario B">']
    for t in ticks:
        x = left + t * scale
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height - 22}" class="grid"/>'
                     f'<text x="{x:.1f}" y="{height - 6}" class="tick" text-anchor="middle">{num(t, 0)}</text>')
    for r, (comp, label) in enumerate(COMPONENTS):
        y = top + r * row_h + 12
        parts.append(f'<text x="{left - 14}" y="{y + 18}" class="axis-label" text-anchor="end">{label}</text>')
        for j, (k, color) in enumerate((("A", COLOR_A), ("B", COLOR_B))):
            v = costs[k]["totals"][comp]
            w = max(v * scale, 1)
            yy = y + j * 16
            parts.append(f'<path d="M{left},{yy} h{w - 4:.1f} a4,4 0 0 1 4,4 v4 a4,4 0 0 1 -4,4 h{-(w - 4):.1f} z" '
                         f'fill="{color}" class="bar" data-tip="{label}, Scenario {k}: {num(v)} €"/>'
                         f'<text x="{left + w + 6:.1f}" y="{yy + 10}" class="bar-value">{num(v)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def sensitivity_chart(sens, index):
    width, height, left, right, top, bottom = 1100, 380, 64, 96, 40, 52
    rows = sens["rows"]
    xs = [r["value"] for r in rows]
    ys = [r["cost_a"] for r in rows] + [r["cost_b"] for r in rows]
    yt = nice_ticks(min(ys) * 0.96, max(ys) * 1.02, 5)
    x_lo, x_hi, y_lo, y_hi = xs[0], xs[-1], yt[0], yt[-1]
    pw, ph = width - left - right, height - top - bottom

    def px(v):
        return left + (v - x_lo) / ((x_hi - x_lo) or 1) * pw

    def py(v):
        return top + ph - (v - y_lo) / ((y_hi - y_lo) or 1) * ph

    data = {"x": xs, "a": [r["cost_a"] for r in rows], "b": [r["cost_b"] for r in rows],
            "x0": x_lo, "x1": x_hi, "y0": y_lo, "y1": y_hi, "left": left, "top": top, "pw": pw, "ph": ph,
            "label": sens["label"]}
    parts = [f'<svg class="chart sens-chart" viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="Costo totale dei due scenari al variare di: {escape(sens["label"])}" '
             f"data-series='{escape(json.dumps(data))}'>"]
    for t in yt:
        parts.append(f'<line x1="{left}" y1="{py(t):.1f}" x2="{left + pw}" y2="{py(t):.1f}" class="grid"/>'
                     f'<text x="{left - 10}" y="{py(t) + 4:.1f}" class="tick" text-anchor="end">{num(t, 0)}</text>')
    stride = max(1, math.ceil(len(xs) / 8))
    for v in xs[::stride]:
        parts.append(f'<text x="{px(v):.1f}" y="{top + ph + 20}" class="tick" text-anchor="middle">{num(v, 2)}</text>')
    parts.append(f'<text x="{left + pw / 2:.1f}" y="{height - 8}" class="axis-label" text-anchor="middle">'
                 f'{escape(sens["label"])}</text>')
    parts.append(f'<text x="{left}" y="{top - 20}" class="tick">€/giorno</text>')

    # Area tra le due rette: la differenza di costo
    band = " ".join(f"{px(r['value']):.1f},{py(r['cost_a']):.1f}" for r in rows) + " " + \
           " ".join(f"{px(r['value']):.1f},{py(r['cost_b']):.1f}" for r in reversed(rows))
    parts.append(f'<polygon points="{band}" class="gap"/>')

    base = sens["base_value"]
    if x_lo <= base <= x_hi:
        parts.append(f'<line x1="{px(base):.1f}" y1="{top}" x2="{px(base):.1f}" y2="{top + ph}" class="base-line"/>'
                     f'<text x="{px(base) + 6:.1f}" y="{top + 12}" class="tick">valore base {num_param(base)}</text>')
    for key, color in (("cost_a", COLOR_A), ("cost_b", COLOR_B)):
        pts = " ".join(f"{px(r['value']):.1f},{py(r[key]):.1f}" for r in rows)
        parts.append(f'<polyline points="{pts}" class="line" stroke="{color}"/>')
        end = rows[-1]
        parts.append(f'<circle cx="{px(end["value"]):.1f}" cy="{py(end[key]):.1f}" r="4.5" fill="{color}" class="end-dot"/>'
                     f'<text x="{px(end["value"]) + 10:.1f}" y="{py(end[key]) + 4:.1f}" class="end-label">'
                     f'{"A" if key == "cost_a" else "B"} · {num(end[key], 0)}</text>')
    if sens["breakeven_in_range"]:
        be = sens["breakeven"]
        cost_be = rows[0]["cost_b"] + (rows[-1]["cost_b"] - rows[0]["cost_b"]) * (be - x_lo) / ((x_hi - x_lo) or 1)
        parts.append(f'<line x1="{px(be):.1f}" y1="{top}" x2="{px(be):.1f}" y2="{top + ph}" class="be-line"/>'
                     f'<circle cx="{px(be):.1f}" cy="{py(cost_be):.1f}" r="6" class="be-dot"/>'
                     f'<text x="{px(be) - 8:.1f}" y="{py(cost_be) - 14:.1f}" class="be-label" text-anchor="end">'
                     f'pareggio {num(be, 2)}</text>')
    parts.append(f'<g class="hover" aria-hidden="true"><line class="hover-line" x1="0" y1="{top}" x2="0" y2="{top + ph}"/>'
                 f'<circle class="hover-a" r="5" fill="{COLOR_A}"/><circle class="hover-b" r="5" fill="{COLOR_B}"/></g>'
                 f'<rect class="hit" x="{left}" y="{top}" width="{pw}" height="{ph}"/>')
    parts.append("</svg>")
    return "".join(parts)


def sensitivity_message(s):
    if s["breakeven"] is None:
        return "La differenza di costo non dipende da questo parametro: non esiste un punto di pareggio."
    if s["breakeven_in_range"]:
        return (f"Le due rette si incrociano a <b>{tagged('breakeven.' + s['parameter'], num(s['breakeven'], 2))}</b>: "
                f"oltre questo valore lo scenario più conveniente cambia.")
    if s["breakeven_meaningful"]:
        return (f"Nessun pareggio nell'intervallo: le rette si incrocerebbero solo a {num(s['breakeven'], 2)}, "
                f"fuori dai valori plausibili considerati.")
    return "Nessun pareggio nell'intervallo, né per alcun valore positivo del parametro: la scelta non cambia."


def section_economics(results, costs_cfg):
    costs, comp = results["costs"], results["costs"]["comparison"]
    common, vt = costs_cfg["common"], costs_cfg["vehicle_types"]
    dist_cmp = results["distance_comparison"]

    table_rows = "".join(
        f"<tr><td>{label}</td><td class='n'>{num(costs['A']['totals'][c])}</td>"
        f"<td class='n'>{num(costs['B']['totals'][c])}</td>"
        f"<td class='n delta'>{('+' if costs['B']['totals'][c] - costs['A']['totals'][c] > 0 else '')}"
        f"{num(costs['B']['totals'][c] - costs['A']['totals'][c])}</td></tr>"
        for c, label in COMPONENTS)

    tabs, panels = [], []
    for i, s in enumerate(results["sensitivity"]):
        short = s["label"].split(" (")[0]
        tabs.append(f'<button type="button" data-sens-btn="{i}" aria-pressed="{"true" if i == 0 else "false"}">'
                    f'{escape(short)}</button>')
        rows = "".join(
            f"<tr><td class='n'>{num(r['value'], 2)}</td><td class='n'>{num(r['cost_a'])}</td>"
            f"<td class='n'>{num(r['cost_b'])}</td><td class='n'>{num(r['diff_b_minus_a'])}</td>"
            f"<td>{r['cheaper']}</td></tr>" for r in s["rows"])
        panels.append(f"""
      <div class="sens-panel" data-sens-panel="{i}">
        <p class="sens-title">{escape(s['label'])}</p>
        <p class="sens-msg">Intervallo {num(s['rows'][0]['value'], 2)}–{num(s['rows'][-1]['value'], 2)}, valore base
        {num_param(s['base_value'])}. {sensitivity_message(s)}</p>
        <div class="scroll-x">{sensitivity_chart(s, i)}</div>
        <details class="more"><summary>Tabella dei valori</summary><div class="table-wrap"><table>
          <thead><tr><th class='n'>Valore</th><th class='n'>Costo A (€)</th><th class='n'>Costo B (€)</th>
          <th class='n'>B − A (€)</th><th>Più conveniente</th></tr></thead><tbody>{rows}</tbody></table></div></details>
      </div>""")

    cheaper_txt = {"A": "Scenario A · un veicolo", "B": "Scenario B · due veicoli", "pari": "Nessuno · costi uguali"}
    return f"""
<section id="economia" class="section">
  {section_head("04", "Analisi economica", "Quanto costa ogni giornata di consegne",
                "I percorsi sono scelti minimizzando la distanza; solo dopo vengono confrontati i costi. "
                "Il percorso più corto non coincide necessariamente con la soluzione più economica.")}
  <div class="duel reveal">
    <div class="duel-side" style="--c:{COLOR_A}"><span><i></i>Scenario A</span><b>{eur(comp['cost_a'])}</b>
      <small>{km(results['scenario_A']['distance_km'])} · 1 veicolo</small></div>
    <div class="duel-mid"><span>Differenza</span><b>{tagged('cmp.abs_diff', eur(comp['abs_diff']))}</b>
      <small>B rispetto ad A: {tagged('cmp.pct_diff', num(comp['pct_diff_vs_a']) + '&nbsp;%')} sul costo,
      {tagged('dist.pct_diff', num(dist_cmp['pct_diff_vs_a']) + '&nbsp;%')} sulla distanza</small>
      <em>{tagged('cmp.cheaper', cheaper_txt[comp['cheaper']])} più conveniente</em></div>
    <div class="duel-side" style="--c:{COLOR_B}"><span><i></i>Scenario B</span><b>{eur(comp['cost_b'])}</b>
      <small>{km(results['scenario_B']['distance_km'])} · 2 veicoli</small></div>
  </div>
  <div class="econ-grid reveal">
    <div>
      <p class="mini-title">Da dove nasce la differenza (€/giorno)</p>
      <div class="legend"><span><i style="background:{COLOR_A}"></i>Scenario A</span>
        <span><i style="background:{COLOR_B}"></i>Scenario B</span></div>
      <div class="scroll-x">{component_chart(costs)}</div>
    </div>
    <div>
      <div class="table-wrap"><table class="cost-table">
        <thead><tr><th>Voce (€/giorno)</th><th class='n'>A</th><th class='n'>B</th><th class='n'>B − A</th></tr></thead>
        <tbody>{table_rows}
          <tr class="total"><td>Totale</td><td class='n'>{num(comp['cost_a'])}</td><td class='n'>{num(comp['cost_b'])}</td>
          <td class='n delta'>{('+' if comp['diff_b_minus_a'] > 0 else '')}{num(comp['diff_b_minus_a'])}</td></tr>
        </tbody></table></div>
      <dl class="assumptions">
        <div class="observed"><dt>Gasolio (osservato)</dt><dd>{num_param(common['fuel_price_eur_per_l'])} €/l</dd></div>
        <div><dt>Autista</dt><dd>{num(common['driver_cost_eur_per_h'], 2)} €/h</dd></div>
        <div><dt>Velocità media</dt><dd>{num(common['average_speed_kmh'], 0)} km/h</dd></div>
        <div><dt>Scarico per consegna</dt><dd>{num(common['service_time_min_per_stop'], 0)} min</dd></div>
        <div><dt>Costo fisso A / B</dt><dd>{num(vt['scenario_A']['fixed_cost_eur_per_day'], 0)} / {num(vt['scenario_B']['fixed_cost_eur_per_day'], 0)} €/giorno</dd></div>
        <div><dt>Consumo A / B</dt><dd>{num(vt['scenario_A']['fuel_consumption_l_per_km'], 2)} / {num(vt['scenario_B']['fuel_consumption_l_per_km'], 2)} l/km</dd></div>
        <div><dt>Altri costi A / B</dt><dd>{num(vt['scenario_A']['other_variable_cost_eur_per_km'], 2)} / {num(vt['scenario_B']['other_variable_cost_eur_per_km'], 2)} €/km</dd></div>
      </dl>
      <p class="note"><b>Prezzo osservato:</b> {escape(costs_cfg.get('parameter_types', {}).get('fuel_price_eur_per_l', 'ipotesi'))}.
      Gli altri parametri sono ipotesi a scopo didattico (data/costs.json), non tariffe ufficiali né dati aziendali.
      Il carburante è calcolato come km × consumo × prezzo; gli altri costi al km lo escludono, senza doppio conteggio.
      I tempi derivano dalla velocità media ipotizzata, non da misure.</p>
    </div>
  </div>
  <div class="sens reveal">
    <div class="sens-head"><p class="mini-title">Analisi di sensibilità · un prezzo alla volta, percorsi invariati</p>
      <div class="chips" role="group" aria-label="Parametro analizzato">{''.join(tabs)}</div></div>
    {''.join(panels)}
    <div class="legend"><span><i style="background:{COLOR_A}"></i>Scenario A</span>
      <span><i style="background:{COLOR_B}"></i>Scenario B</span><span><i class="swatch-gap"></i>differenza B − A</span></div>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# Metodologia, conclusioni, pagina
# ---------------------------------------------------------------------------

def section_method(instance, results):
    n = len(instance.clients)
    b = results["scenario_B"]
    status = instance.config["distance_data"]
    check = results.get("distance_check")
    check_text = ""
    if check:
        check_text = (f" Controllo indipendente del motore di calcolo con Valhalla (stessi dati OpenStreetMap): "
                      f"{check['pairs'] - check['missing']} coppie su {check['pairs']} confrontate, differenza media "
                      f"{num(check['mean_abs_diff_km'], 2)} km, massima {num(check['max_abs_diff_km'], 2)} km; "
                      f"la matrice OSRM resta la fonte principale.")
    return f"""
<section id="metodo" class="section">
  {section_head("05", "Metodologia", "Come sono stati ottenuti i risultati")}
  <ol class="method reveal">
    <li><span class="m-n">01</span><h3>Enumerazione completa</h3>
      <p>Il programma individua, mediante enumerazione completa, i percorsi che minimizzano la distanza complessiva
      per ciascuna configurazione di flotta; successivamente le soluzioni ottenute vengono confrontate con un modello
      economico parametrico. Nessuna euristica: ogni soluzione ammissibile viene valutata, quindi il risultato è ottimo
      rispetto alla distanza. Con un veicolo le sequenze sono {n}! = {math.factorial(n)}; con due veicoli identici le
      ripartizioni dei clienti sono 2<sup>{n - 1}</sup> − 1 = {2 ** (n - 1) - 1}, ciascuna con tutti gli ordini di visita.</p></li>
    <li><span class="m-n">02</span><h3>Vincoli di capacità</h3>
      <p>Il carico di ogni veicolo non può superare la sua capacità: Σ q<sub>i</sub> ≤ Q. Nello Scenario B
      {b['partitions_examined'] - b['feasible_partitions']} ripartizioni su {b['partitions_examined']} sono scartate per
      questo motivo. Ogni cliente è servito esattamente una volta ed entrambi i veicoli sono usati.</p></li>
    <li><span class="m-n">03</span><h3>Modello dei costi</h3>
      <p class="formula">C = F + km · (consumo · prezzo + altri costi) + costo orario · (km / velocità + consegne · tempo di scarico)</p>
      <p>Il costo è calcolato sui percorsi ottimi in distanza, non minimizzato direttamente. Il costo di uno scenario
      è la somma dei suoi veicoli ed è lineare in ogni prezzo, quindi il punto di pareggio si calcola in forma esatta.</p></li>
    <li><span class="m-n">04</span><h3>Origine dei dati</h3>
      <p>Distanze stradali {'documentate' if status['status'] == 'VERIFIED' else 'NON documentate'}, calcolate da un servizio
      di routing (non misurate sul campo): motore OSRM sulla rete OpenStreetMap, percorso più rapido in auto, interrogazione del
      {escape('/'.join(reversed((status.get('retrieved_on') or '').split('-'))))}. La matrice è direzionale: andata e
      ritorno possono differire.{check_text} Clienti, quantità e costi sono ipotesi didattiche.</p></li>
  </ol>
</section>"""


def section_conclusions(instance, results):
    comp = results["costs"]["comparison"]
    dist_cmp = results["distance_comparison"]
    shorter = "A" if dist_cmp["distance_a_km"] <= dist_cmp["distance_b_km"] else "B"
    in_range = [s for s in results["sensitivity"] if s["breakeven_in_range"]]
    stable = [s for s in results["sensitivity"] if not s["breakeven_in_range"]]
    names = {"A": "un solo veicolo", "B": "due veicoli"}
    text = [f"Con i dati attuali {names[shorter]} percorre meno strada"]
    if comp["cheaper"] == shorter:
        text.append(f" ed è anche la soluzione più economica: la distanza e il costo portano alla stessa scelta.")
    else:
        text.append(f", ma la soluzione più economica è {names.get(comp['cheaper'], 'nessuna delle due')}.")
    def name(s):        # "Prezzo del carburante (EUR/l)" -> "prezzo del carburante"
        label = s["label"].split(" (")[0]
        return escape(label[0].lower() + label[1:])

    def unit(s):        # "(EUR/l)" -> "€/l"
        return escape(s["label"].split(" (")[-1].rstrip(")").replace("EUR", "€")) if " (" in s["label"] else ""

    if stable:
        text.append(" La conclusione non cambia al variare del " +
                    " e del ".join(name(s) for s in stable) + " negli intervalli considerati")
    if in_range:
        text.append("; si inverte invece se il " +
                    "; ".join(f"{name(s)} supera {num(s['breakeven'], 2)}&nbsp;{unit(s)}" for s in in_range))
    text.append(". A decidere il confronto sono soprattutto i costi fissi della flotta più che i chilometri.")
    return f"""
<section id="conclusioni" class="section">
  {section_head("06", "Conclusioni", "Cosa dicono i numeri")}
  <div class="conclusion reveal">
    <p class="conclusion-text">{''.join(text)}</p>
    <div class="limits">
      <p class="mini-title">Limiti</p>
      <ul><li>Costi e velocità sono ipotesi; nessun traffico, finestra oraria o vincolo di orario di lavoro.</li>
      <li>Percorsi ottimizzati sulla distanza, non direttamente sul costo.</li>
      <li>L'enumerazione completa cresce in modo fattoriale: adatta solo a istanze piccole come questa.</li></ul>
    </div>
  </div>
</section>"""


def build_html(instance, results, costs_cfg):
    company = instance.config["company"]
    status = instance.config["distance_data"]
    comp = results["costs"]["comparison"]
    a, b = results["scenario_A"], results["scenario_B"]
    verified = status["status"] == "VERIFIED"
    date = "/".join(reversed((status.get("retrieved_on") or "").split("-")))
    status_pill = (f'<span class="status ok"><i></i>Distanze OSRM documentate<span class="status-date">&nbsp;· {escape(date)}</span></span>' if verified else
                   '<span class="status warn"><i></i>Distanze non verificate</span>')
    banner = "" if verified else (f'<div class="banner wrap"><b>Attenzione:</b> le distanze non sono verificate. '
                                  f'{escape(status["source"])}</div>')
    total_kg = sum(instance.demand.values())
    shortest = min(a["distance_km"], b["distance_km"])
    cheaper = comp["cheaper"]
    cheaper_name = {"A": "un veicolo", "B": "due veicoli", "pari": "pari"}[cheaper]
    saving_pct = comp["abs_diff"] / max(comp["cost_a"], comp["cost_b"]) * 100
    area = company.get("area", "")

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SiciliaFresh · Percorsi di consegna</title>
<meta name="description" content="Pianificazione e confronto economico dei percorsi di consegna di un'impresa agroalimentare (Project Work PW 23, L-31).">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600&display=swap">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<a class="skip" href="#percorsi">Vai ai percorsi</a>
<header class="topbar">
  <div class="wrap topbar-in">
    <a class="logo" href="#top" aria-label="SiciliaFresh, inizio pagina">
      <svg viewBox="0 0 30 20" aria-hidden="true"><path d="M3 14 C 9 4, 15 4, 15 10 S 21 16, 27 6" /><circle cx="3" cy="14" r="2.6"/><circle cx="27" cy="6" r="2.6"/></svg>
      <span>Sicilia<b>Fresh</b></span></a>
    <nav aria-label="Sezioni"><a href="#overview">Sintesi</a><a href="#percorsi">Percorsi</a><a href="#dati">Dati</a>
      <a href="#economia">Economia</a><a href="#metodo">Metodo</a><a href="#conclusioni">Conclusioni</a></nav>
    {status_pill}
  </div>
</header>
{banner}
<main id="top">
<section class="hero wrap">
  <p class="eyebrow hero-eyebrow">Project Work 23 · L-31 Informatica per le Aziende Digitali</p>
  <h1 class="reveal">Cinque consegne lungo la costa.<br><span>Uno o due furgoni?</span></h1>
  <div class="hero-meta reveal">
    <p class="lead">{escape(company['name'])} è un distributore agroalimentare simulato. Il prototipo calcola con
    l'enumerazione completa i percorsi più brevi con uno e con due veicoli, poi ne confronta i costi giornalieri.</p>
    <dl>
      <div><dt>Area</dt><dd>{escape(area)}</dd></div>
      <div><dt>Deposito</dt><dd>{escape(instance.names[instance.depot])}</dd></div>
      <div><dt>Clienti</dt><dd>{escape(', '.join(instance.names[c] for c in instance.clients))}</dd></div>
    </dl>
  </div>
  <figure class="coast-fig reveal"><div class="scroll-x">{coast_strip(instance)}</div>
    <figcaption>Ovest → est: posizione proporzionale alla longitudine reale; l'altezza delle barre indica i kg richiesti da ciascun cliente.</figcaption>
  </figure>
</section>

<section id="overview" class="section wrap-section">
  {section_head("01", "Sintesi", "Il risultato in breve")}
  <div class="overview reveal">
    <div class="ov-main">
      <p class="ov-label">Risparmio giornaliero con {cheaper_name}</p>
      <p class="ov-hero">{counter(comp['abs_diff'], 2)}<span class="unit">€</span></p>
      <p class="ov-text">Lo Scenario {cheaper} costa {eur(min(comp['cost_a'], comp['cost_b']))} al giorno contro
      {eur(max(comp['cost_a'], comp['cost_b']))}: {num(saving_pct, 1)}&nbsp;% in meno.</p>
    </div>
    <dl class="ov-list">
      <div><dt>Clienti serviti</dt><dd>{counter(len(instance.clients), 0)}</dd></div>
      <div><dt>Quantità distribuita</dt><dd>{counter(total_kg, 0)}<small>kg</small></dd></div>
      <div><dt>Distanza ottimale</dt><dd>{counter(shortest, 2)}<small>km</small></dd></div>
      <div class="ov-win" style="--c:{COLOR_A if cheaper == 'A' else COLOR_B}"><dt>Scenario più conveniente</dt>
        <dd><i></i>{'Scenario ' + cheaper if cheaper != 'pari' else 'Pari'}<small>{cheaper_name}</small></dd></div>
    </dl>
  </div>
</section>
{section_explorer(instance, results)}
{section_data(instance, results)}
{section_economics(results, costs_cfg)}
{section_method(instance, results)}
{section_conclusions(instance, results)}
</main>
<footer class="footer"><div class="wrap">
  <p><b>SiciliaFresh</b> · prototipo didattico. Azienda, clienti, quantità e costi simulati; località e distanze reali.</p>
  <p>Pagina generata da <code>main.py</code> il {escape(results['generated_at'])} · dati completi in
  <a href="results.json">results.json</a></p>
</div></footer>
<div class="tooltip" role="status" aria-live="polite" hidden></div>
<script src="app.js" defer></script>
</body>
</html>
"""
