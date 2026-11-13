"""Experimentos de los requerimientos 1 a 4 siguiendo el protocolo de la sección 6 del enunciado.
Todos los resultados se guardan en results/ (CSV/JSON); las tablas y gráficas se generan desde esos archivos."""
import csv, gc, json, os, platform, random, statistics, sys, time
import numpy as np
from scipy.spatial import ConvexHull

from . import catalog
from .geo import to_utm, from_utm
from .model import build_graph, to_networkx, largest_component, associate_places, memory_estimates, RoadGraph
from .shortest import dijkstra_linear, dijkstra_heap
from .hull import quickhull
from .tsp import brute_force, held_karp, nearest_neighbor, sub_matrix, held_karp_memory_bytes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, PROC = os.path.join(ROOT, "results"), os.path.join(ROOT, "data", "processed")
SEED = 42
REPS, LONG_S, LIMIT_S = 5, 60.0, 300.0           # repeticiones, "más de un minuto", límite de 5 minutos
DAY_S = 11 * 3600


# ------------------------------------------------------------------ utilidades
def measure(fn, reps=REPS):
    """Mediana de `reps` ejecuciones (una sola si la primera pasa de un minuto). Solo mide fn()."""
    runs, out = [], None
    for i in range(reps):
        gc.collect(); gc.disable()
        t = time.perf_counter_ns(); out = fn(); dt = (time.perf_counter_ns() - t) / 1e6
        gc.enable()
        runs.append(dt)
        if dt / 1000 > LONG_S:
            break
    return statistics.median(runs), out, len(runs)


def write_csv(name, header, rows):
    with open(os.path.join(RES, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


def write_json(name, obj):
    with open(os.path.join(RES, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=float)


def read_json(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return json.load(f)


def environment(source):
    cpu = "?"
    try:
        cpu = next(l.split(":")[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    except Exception:
        cpu = platform.processor()
    ram = "?"
    try:
        ram = f"{int(next(l for l in open('/proc/meminfo') if l.startswith('MemTotal')).split()[1]) / 1048576:.1f} GB"
    except Exception:
        pass
    import scipy, networkx
    env = {"procesador": cpu, "nucleos": os.cpu_count(), "ram": ram, "so": platform.platform(),
           "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
           "networkx": networkx.__version__, "fuente_datos": source, "semilla": SEED,
           "repeticiones": REPS, "limite_s": LIMIT_S}
    try:
        import osmnx; env["osmnx"] = osmnx.__version__
    except ImportError:
        env["osmnx"] = "no instalado"
    return env


def get_raw(source):
    if source == "synthetic":
        from .synth import generate
        return generate(), "sintética (semilla 7)"
    from .osm_source import download_department
    return download_department()


def load_graph():
    g = RoadGraph.load(os.path.join(PROC, "graph.npz"))
    places = catalog.load()
    pn = {r["id"]: r for r in csv.DictReader(open(os.path.join(PROC, "places_nodes.csv"), encoding="utf-8"))}
    for p in places:
        p["node"] = int(pn[p["id"]]["nodo"]); p["dist_nodo_m"] = float(pn[p["id"]]["dist_nodo_m"])
    return g, places


# ------------------------------------------------------------------ R1
def run_r1(source):
    os.makedirs(RES, exist_ok=True); os.makedirs(PROC, exist_ok=True)
    raw, fecha = get_raw(source)
    env = environment(source); env["fecha_descarga_o_generacion"] = fecha
    write_json("environment.json", env)

    g, st = build_graph(raw)
    g.save(os.path.join(PROC, "graph.npz"))
    places = catalog.load()
    node, dist = associate_places(g, places)
    write_csv("places_nodes.csv",
              ["id", "nombre", "categoria", "nodo", "osm_id_nodo", "dist_nodo_m", "mayor_500m"],
              [[p["id"], p["nombre"], p["categoria"], int(n), int(g.ids[n]), round(float(d), 1), int(d > 500)]
               for p, n, d in zip(places, node, dist)])
    with open(os.path.join(PROC, "places_nodes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "nodo", "dist_nodo_m"])
        for p, n, d in zip(places, node, dist):
            w.writerow([p["id"], int(n), round(float(d), 3)])
    catalog.save_csv(os.path.join(PROC, "catalog.csv"))

    mem = memory_estimates(g.V, g.E)
    write_json("r1_resumen.json", {"estadisticas": st, "memoria": mem,
                                    "lugares_mas_500m": [p["id"] for p, d in zip(places, dist) if d > 500],
                                    "dist_max_m": float(dist.max()), "dist_media_m": float(dist.mean())})

    # tiempo de largest_component en redes de tamaño creciente (radios alrededor de la plaza de Bolívar)
    center = to_utm(*catalog_start_latlon(places))
    rows = []
    for name, km in [("Radio de 2 km", 2), ("Radio de 5 km", 5), ("Radio de 10 km", 10), ("Radio de 20 km", 20),
                     ("Departamento completo", None)]:
        if km is None:
            r = raw
        elif source == "synthetic":
            from .synth import subset_bbox
            r = subset_bbox(raw, (float(center[0]), float(center[1])), km * 1000)
        else:
            from .osm_source import download_radius
            r = download_radius(km)
        G = to_networkx(r)                               # fuera de la medición
        ms, (H, impl), n = measure(lambda: largest_component(G, strongly=True))
        V, E = G.number_of_nodes(), G.number_of_edges()
        rows.append([name, V, E, V + E, round(ms, 3), n, impl, H.number_of_nodes(), H.number_of_edges()])
        print("R1", name, V, E, round(ms, 2), "ms")
    write_csv("r1_tiempos.csv", ["red", "V", "E", "V+E", "tiempo_ms", "repeticiones", "implementacion",
                                 "V_componente", "E_componente"], rows)
    return g


def catalog_start_latlon(places):
    s = next(p for p in places if p["id"] == catalog.START_ID)
    return s["lat"], s["lon"]


# ------------------------------------------------------------------ R2
def run_r2():
    g, places = load_graph()
    lists, V = g.lists, g.V
    rng = random.Random(SEED)
    idx = range(len(places))
    cand = [(i, j) for i in idx for j in idx if i != j and places[i]["node"] != places[j]["node"]]
    near = [(i, j) for (i, j) in cand if catalog.are_close(places[i], places[j])]
    far = [(i, j) for (i, j) in cand if not catalog.are_close(places[i], places[j])]
    rng.shuffle(near); rng.shuffle(far)
    pairs_near, pairs_far = near[:10], far[:10]
    rows, both = [], {}
    for (i, j) in pairs_near + pairs_far:
        s, t = places[i]["node"], places[j]["node"]
        ms, r, _ = measure(lambda: dijkstra_heap(lists, V, s, t))
        rows.append([places[i]["id"], places[j]["id"], "cola_prioridad", round(r.time, 3), r.explored, round(ms, 3)])
        both[(i, j)] = r.time
    for (i, j) in pairs_near:
        s, t = places[i]["node"], places[j]["node"]
        ms, r, _ = measure(lambda: dijkstra_linear(lists, V, s, t))
        assert abs(r.time - both[(i, j)]) < 1e-6, "las dos versiones difieren"        # verificación
        rows.append([places[i]["id"], places[j]["id"], "lineal", round(r.time, 3), r.explored, round(ms, 3)])
        print("R2 lineal", places[i]["id"], places[j]["id"], round(ms, 1), "ms")
    write_csv("r2_dijkstra.csv", ["origen", "destino", "version", "tiempo_viaje_s", "nodos_explorados", "tiempo_ms"], rows)

    # cociente lineal / cola en los 10 pares comunes
    t_heap = {(r[0], r[1]): r[5] for r in rows if r[2] == "cola_prioridad"}
    ratios = [r[5] / t_heap[(r[0], r[1])] for r in rows if r[2] == "lineal"]
    write_json("r2_cociente.json", {"n_pares": len(ratios), "mediana": statistics.median(ratios),
                                    "minimo": min(ratios), "maximo": max(ratios),
                                    "verificacion_tiempos_iguales": True})

    # matriz de tiempos entre todos los lugares: Dijkstra con cola, sin destino, una vez desde cada lugar
    nodes = [p["node"] for p in places]
    t0 = time.perf_counter()
    M = []
    for s in nodes:
        d = dijkstra_heap(lists, V, s).dist
        M.append([d[t] for t in nodes])
    t_mat = (time.perf_counter() - t0) * 1000
    ids = [p["id"] for p in places]
    write_csv("matriz_tiempos.csv", [""] + ids, [[ids[i]] + [round(x, 3) for x in M[i]] for i in range(len(ids))])
    asym = max(abs(M[i][j] - M[j][i]) for i in range(len(M)) for j in range(len(M)))
    write_json("r2_matriz_info.json", {"n": len(ids), "tiempo_total_ms": t_mat, "max_asimetria_s": asym,
                                       "max_s": max(max(r) for r in M), "hay_infinitos": any(x == float("inf") for r in M for x in r)})
    return M


def load_matrix():
    with open(os.path.join(RES, "matriz_tiempos.csv"), encoding="utf-8") as f:
        rd = list(csv.reader(f))
    ids = rd[0][1:]
    return ids, [[float(x) for x in r[1:]] for r in rd[1:]]


# ------------------------------------------------------------------ R3
def run_r3():
    g, _ = load_graph()
    sets = []
    pts = {(int(round(x)), int(round(y))) for x, y in zip(g.x, g.y)}      # enteros y sin repetidos
    sets.append(("Nodos de la red", sorted(pts)))
    for n in (1000, 10000, 50000):
        rs = np.random.default_rng(SEED)
        sq = {tuple(p) for p in rs.integers(0, 100_000, size=(n, 2)).tolist()}
        sets.append(("Cuadrado, " + f"{n:,}".replace(",", " ") + " puntos", sorted(sq)))
    rows, hull_net = [], None
    for name, pts in sets:
        arr = np.array(pts, dtype=np.int64)
        random.Random(SEED).shuffle(pts)                                  # el orden de entrada no debe ayudar
        ms_own, h, _ = measure(lambda: quickhull(pts))
        ms_sp, ch, _ = measure(lambda: ConvexHull(arr))
        ref = {tuple(p) for p in arr[ch.vertices].tolist()}
        same = set(h) == ref
        assert same, f"las envolventes difieren en {name}"
        rows.append([name, len(pts), len(h), round(ms_own, 3), round(ms_sp, 3), round(ms_own / ms_sp, 1), int(same)])
        print("R3", name, len(pts), len(h), round(ms_own, 1), round(ms_sp, 2))
        if hull_net is None:
            hull_net = h
    write_csv("r3_envolvente.csv", ["conjunto", "n", "vertices", "tiempo_propio_ms", "tiempo_scipy_ms", "cociente", "mismos_vertices"], rows)
    hx, hy = np.array([p[0] for p in hull_net], float), np.array([p[1] for p in hull_net], float)
    la, lo = from_utm(hx, hy)
    write_json("r3_hull_red.json", {"utm": [list(p) for p in hull_net],
                                    "latlon": [[float(a), float(b)] for a, b in zip(la, lo)]})
    return rows


# ------------------------------------------------------------------ R4
def instance(places_ids, ids, k, seed, start=catalog.START_ID):
    rng = random.Random(seed)
    others = [i for i in places_ids if i != start]
    return [start] + rng.sample(others, k)


def run_r4(kmax=12, extra_hk=(13, 14, 15, 16)):
    ids, M = load_matrix()
    pos = {p: i for i, p in enumerate(ids)}
    def D_of(sel): return sub_matrix(M, [pos[x] for x in sel])
    rows = []
    for k in range(5, kmax + 1):
        sel = instance(ids, ids, k, 1000 + k)
        D = D_of(sel)
        ms_hk, (c_hk, t_hk), _ = measure(lambda: held_karp(D))
        ms_bf, res, n = measure_bf(D)
        if res is None:
            bf_ms, bf_cost = "no completada", ""
        else:
            bf_ms, bf_cost = round(ms_bf, 3), round(res[0], 3)
            assert abs(res[0] - c_hk) < 1e-6, "fuerza bruta y Held-Karp difieren"
        rows.append([k, bf_ms, round(ms_hk, 3), round(c_hk, 3), bf_cost, held_karp_memory_bytes(k)])
        print("R4 k=", k, "BF", bf_ms, "HK", round(ms_hk, 2), flush=True)
        write_csv("r4_exactas.csv", ["k", "tiempo_fuerza_bruta_ms", "tiempo_held_karp_ms", "optimo_s", "optimo_fb_s", "memoria_tabla_bytes"], rows)
    extra = []
    for k in extra_hk:
        sel = instance(ids, ids, k, 1000 + k)
        ms_hk, (c, _), _ = measure(lambda: held_karp(D_of(sel)))
        extra.append([k, round(ms_hk, 3), held_karp_memory_bytes(k)])
        print("R4 extra HK k=", k, round(ms_hk, 1), flush=True)
    write_csv("r4_held_karp_extra.csv", ["k", "tiempo_held_karp_ms", "memoria_tabla_bytes"], extra)

    # calidad de la heurística
    qrows, worst = [], None
    for k in (5, 8, 10, 12):
        for i in range(10):
            sel = instance(ids, ids, k, 50000 + 100 * k + i)
            D = D_of(sel)
            opt, t_opt = held_karp(D); gr, t_gr = nearest_neighbor(D)
            gap = 100 * (gr - opt) / opt
            qrows.append([k, i, round(opt, 3), round(gr, 3), round(gap, 3)])
            if worst is None or gap > worst["gap"]:
                worst = {"k": k, "gap": gap, "sel": sel, "opt": opt, "greedy": gr,
                         "tour_opt": [sel[x] for x in t_opt], "tour_greedy": [sel[x] for x in t_gr]}
    write_csv("r4_heuristica_instancias.csv", ["k", "instancia", "optimo_s", "voraz_s", "brecha_pct"], qrows)
    write_json("r4_peor_caso_heuristica.json", worst)

    run_itinerary(ids, M)


def measure_bf(D):
    """Fuerza bruta con límite de 5 minutos; devuelve (ms, resultado|None, repeticiones)."""
    runs, res = [], None
    for _ in range(REPS):
        gc.collect(); t = time.perf_counter()
        res = brute_force(D, time_limit_s=LIMIT_S)
        dt = (time.perf_counter() - t) * 1000
        if res is None:
            return dt, None, len(runs) + 1
        runs.append(dt)
        if dt / 1000 > LONG_S:
            break
    return statistics.median(runs), res, len(runs)


ITIN_START = catalog.START_ID
ITIN_ATTR = ["A05", "A04", "A06", "A07", "A09", "A10", "A03", "A01"]      # 8 atractivos


def plan(places_by_id, M, ids, start, attr):
    pos = {p: i for i, p in enumerate(ids)}
    sel = [start] + attr
    D = sub_matrix(M, [pos[x] for x in sel])
    c, tour = held_karp(D)
    return c, [sel[x] for x in tour]


def run_itinerary(ids, M):
    places = {p["id"]: p for p in catalog.load()}
    attr, pasos = list(ITIN_ATTR), []
    while True:
        travel, order = plan(places, M, ids, ITIN_START, attr)
        visits = sum(places[a]["visita_min"] for a in attr) * 60
        total = travel + visits
        pasos.append({"atractivos": list(attr), "viaje_s": travel, "visitas_s": visits, "total_s": total, "cabe": total <= DAY_S})
        if total <= DAY_S or len(attr) <= 1:
            break
        # se quita el atractivo cuyo retiro ahorra más tiempo total (visita + desvío); desempata el id
        best = None
        for a in attr:
            rest = [x for x in attr if x != a]
            tr, _ = plan(places, M, ids, ITIN_START, rest)
            saving = (travel + places[a]["visita_min"] * 60) - tr
            if best is None or saving > best[0] + 1e-9:
                best = (saving, a)
        pasos[-1]["se_quita"] = best[1]; pasos[-1]["ahorro_s"] = best[0]
        attr.remove(best[1])
    pos = {p: i for i, p in enumerate(ids)}
    legs, acc = [], 0.0
    for a, b in zip(order, order[1:]):
        mv = M[pos[a]][pos[b]]; vis = places[b]["visita_min"] * 60 if b != ITIN_START else 0
        acc += mv + vis
        legs.append({"de": a, "a": b, "desplazamiento_min": mv / 60, "visita_min": vis / 60, "acumulado_h": acc / 3600})
    sel = [ITIN_START] + attr
    D = sub_matrix(M, [pos[x] for x in sel])
    g_cost, g_tour = nearest_neighbor(D)
    write_json("r4_itinerario.json", {
        "inicio": ITIN_START, "jornada_h": 11, "pasos": pasos, "atractivos_finales": attr, "orden": order,
        "tramos": legs, "viaje_total_s": travel, "visitas_total_s": visits, "duracion_total_s": total,
        "voraz": {"orden": [sel[x] for x in g_tour], "viaje_s": g_cost, "total_s": g_cost + visits}})
