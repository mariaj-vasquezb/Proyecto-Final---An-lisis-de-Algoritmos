"""Gráficas y tablas generadas A PARTIR de los archivos CSV/JSON de results/ (protocolo, punto 8)."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from . import catalog
from .experiments import RES, read_json, load_graph, load_matrix
from .shortest import dijkstra_heap

FIG = os.path.join(RES, "figures")
C1, C2, C3 = "#1b6ca8", "#d1495b", "#2a9d8f"


def _save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, name), dpi=150); plt.close(fig)


def fig_r1():
    d = pd.read_csv(os.path.join(RES, "r1_tiempos.csv"))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(d["V+E"], d["tiempo_ms"], "o-", color=C1, label="medido (mediana de 5)")
    k = (d["tiempo_ms"] / d["V+E"]).iloc[-1]
    xs = np.linspace(0, d["V+E"].max(), 50)
    ax.plot(xs, k * xs, "--", color="gray", label="recta proporcional a V+E (ajustada al último punto)")
    for _, r in d.iterrows():
        ax.annotate(r["red"].replace("Departamento completo", "Depto.").replace("Radio de ", "r="), (r["V+E"], r["tiempo_ms"]),
                    textcoords="offset points", xytext=(4, -12), fontsize=7)
    ax.set_xlabel("Tamaño de la red, V + E"); ax.set_ylabel("Tiempo de largest_component (ms)")
    ax.set_title("R1. Componente fuertemente conexa: tiempo vs V+E"); ax.legend(fontsize=7); ax.grid(alpha=.3)
    _save(fig, "r1_escalamiento.png")


def fig_r2():
    d = pd.read_csv(os.path.join(RES, "r2_dijkstra.csv"))
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for v, c, m, lab in [("lineal", C2, "s", "Lineal  O(V²)"), ("cola_prioridad", C1, "o", "Cola de prioridad  O((V+E) log V)")]:
        s = d[d["version"] == v]
        ax.scatter(s["nodos_explorados"], s["tiempo_ms"], c=c, marker=m, s=34, label=lab, alpha=.85)
    ax.set_yscale("log"); ax.set_xlabel("Nodos explorados"); ax.set_ylabel("Tiempo (ms), escala log")
    ax.set_title("R2. Dijkstra: tiempo vs nodos explorados"); ax.legend(fontsize=8, loc="lower right"); ax.grid(alpha=.3, which="both")
    _save(fig, "r2_dijkstra.png")


def hull_map_axes(ax, g, hull_xy, lw=.15):
    ptr = g.indptr
    src = np.repeat(np.arange(g.V), np.diff(ptr))
    segs = np.stack([np.c_[g.x[src], g.y[src]], np.c_[g.x[g.indices], g.y[g.indices]]], axis=1)
    from matplotlib.collections import LineCollection
    ax.add_collection(LineCollection(segs[::2], colors="#9aa5b1", linewidths=lw))
    ax.set_xlim(g.x.min() - 2000, g.x.max() + 2000); ax.set_ylim(g.y.min() - 2000, g.y.max() + 2000)
    ax.set_aspect("equal")
    if hull_xy is not None:
        h = np.array(hull_xy + [hull_xy[0]], float)
        ax.plot(h[:, 0], h[:, 1], "-", color=C2, lw=1.8, label="Envolvente convexa")
        ax.plot(h[:-1, 0], h[:-1, 1], "o", color=C2, ms=3)


def fig_r3():
    g, places = load_graph()
    hull = [tuple(p) for p in read_json("r3_hull_red.json")["utm"]]
    fig, ax = plt.subplots(figsize=(5.4, 6.4))
    hull_map_axes(ax, g, hull)
    ax.plot([g.x[p["node"]] for p in places], [g.y[p["node"]] for p in places], ".", color=C1, ms=4, label="Lugares del catálogo")
    ax.set_title(f"R3. Envolvente convexa de la red ({len(hull)} vértices)"); ax.legend(fontsize=8, loc="center right")
    ax.set_xlabel("Este UTM 18N (m)"); ax.set_ylabel("Norte UTM 18N (m)"); ax.tick_params(labelsize=7)
    _save(fig, "r3_envolvente_mapa.png")
    d = pd.read_csv(os.path.join(RES, "r3_envolvente.csv"))
    fig, ax = plt.subplots(figsize=(6, 4)); x = np.arange(len(d)); w = .38
    ax.bar(x - w/2, d["tiempo_propio_ms"], w, color=C1, label="Quickhull propio (Python)")
    ax.bar(x + w/2, d["tiempo_scipy_ms"], w, color=C3, label="SciPy ConvexHull (Qhull, C)")
    ax.set_xticks(x); ax.set_xticklabels([f"{c}\nn={n:,}" for c, n in zip(d["conjunto"], d["n"])], fontsize=6.5)
    ax.set_yscale("log"); ax.set_ylabel("Tiempo (ms), escala log"); ax.set_title("R3. Tiempos de la envolvente convexa")
    ax.legend(fontsize=8); ax.grid(alpha=.3, axis="y", which="both")
    _save(fig, "r3_tiempos.png")


def fig_r4():
    d = pd.read_csv(os.path.join(RES, "r4_exactas.csv"))
    fig, ax = plt.subplots(figsize=(6, 4))
    bf = pd.to_numeric(d["tiempo_fuerza_bruta_ms"], errors="coerce")
    ax.plot(d["k"], bf, "s-", color=C2, label="Fuerza bruta  O(k!·k)")
    ax.plot(d["k"], d["tiempo_held_karp_ms"], "o-", color=C1, label="Held-Karp  O(2^k·k²)")
    nc = d[bf.isna()]
    for _, r in nc.iterrows():
        ax.annotate("no completada", (r["k"], d["tiempo_held_karp_ms"].max()), color=C2, fontsize=8)
    ax.set_yscale("log"); ax.set_xlabel("k (lugares a visitar, sin contar la salida)"); ax.set_ylabel("Tiempo (ms), escala log")
    ax.set_title("R4. Soluciones exactas: tiempo vs k"); ax.legend(fontsize=8); ax.grid(alpha=.3, which="both")
    _save(fig, "r4_exactas.png")
    q = pd.read_csv(os.path.join(RES, "r4_heuristica_instancias.csv"))
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ks = sorted(q["k"].unique())
    ax.boxplot([q[q["k"] == k]["brecha_pct"] for k in ks]); ax.set_xticklabels([f"k={k}" for k in ks])
    ax.set_ylabel("Brecha vs. óptimo (%)"); ax.set_title("R4. Calidad del vecino más cercano"); ax.grid(alpha=.3, axis="y")
    _save(fig, "r4_heuristica.png")


def fig_itinerary():
    g, places = load_graph()
    pl = {p["id"]: p for p in places}
    it = read_json("r4_itinerario.json")
    lists = g.lists
    fig, ax = plt.subplots(figsize=(5.6, 6.6))
    hull_map_axes(ax, g, None, lw=.12)
    order = it["orden"]
    for a, b in zip(order, order[1:]):
        path = dijkstra_heap(lists, g.V, pl[a]["node"], pl[b]["node"]).path
        ax.plot(g.x[path], g.y[path], color=C2, lw=1.6, alpha=.9)
    for n, pid in enumerate(order[:-1]):
        p = pl[pid]; ax.plot(g.x[p["node"]], g.y[p["node"]], "o", color=C1, ms=6)
        ax.annotate(f"{n}", (g.x[p["node"]], g.y[p["node"]]), textcoords="offset points", xytext=(4, 4), fontsize=9, weight="bold")
    ax.set_title("Itinerario de un día (Held-Karp); 0 = salida y regreso"); ax.tick_params(labelsize=7)
    _save(fig, "r4_itinerario_mapa.png")


def fig_architecture():
    """Diagrama de componentes con cuadrícula y flechas ortogonales (sin cruces)."""
    fig, ax = plt.subplots(figsize=(7.8, 4.3)); ax.axis("off"); ax.set_xlim(0, 16); ax.set_ylim(0.2, 9.0)
    INK, LINE = "#1f2d27", "#4a5d54"
    tones = {"in": "#eef1ee", "proc": "#e3eef9", "store": "#f6efdc", "app": "#e0f1e8"}

    def box(x, y, w, h, title, lines, tone):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.25", fc=tones[tone], ec=LINE, lw=1.1))
        top = y + h
        ax.text(x + 0.3, top - 0.5, title, fontsize=8.2, fontweight="bold", color=INK, va="center", ha="left")
        for i, t in enumerate(lines):
            ax.text(x + 0.3, top - 1.1 - 0.46 * i, t, fontsize=6.9, color="#34463d", va="center", ha="left")

    def arrow(p, q, label=None, dy=0.3):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=11, color=LINE, lw=1.3, shrinkA=0, shrinkB=0))
        if label:
            ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + dy, label, fontsize=6.6, ha="center", va="bottom", color=INK)

    # columnas: entradas | R1 | R2 y R3 | R4 y R5.  Filas: centro en y=7.55 (arriba) y y=4.85 (abajo)
    box(0.1, 6.4, 2.8, 2.3, "Fuente de la red", ["OSMnx (Quindío)", "o red sintética"], "in")
    box(0.1, 3.7, 2.8, 2.3, "Catálogo", ["40 lugares con", "coordenadas y visitas"], "in")
    box(4.1, 3.7, 3.2, 5.0, "R1  Modelo de la red", ["src/model.py", "tiempos y distancias", "componente fuertemente", "conexa (SCC)", "grafo en listas (CSR)", "lugar \u2192 nodo cercano"], "proc")
    box(8.8, 6.4, 3.0, 2.3, "R2  Caminos mínimos", ["src/shortest.py", "Dijkstra lineal y con cola", "matriz de tiempos 40\u00d740"], "proc")
    box(8.8, 3.7, 3.0, 2.3, "R3  Envolvente", ["src/hull.py", "Quickhull propio vs SciPy"], "proc")
    box(13.1, 6.4, 2.8, 2.3, "R4  Ruta óptima", ["src/tsp.py", "fuerza bruta, Held-Karp,", "voraz e itinerario"], "proc")
    box(13.1, 3.7, 2.8, 2.3, "R5  Aplicación", ["app/index.html", "mapa, rutas, resultados"], "app")
    box(4.1, 0.4, 11.8, 1.9, "Archivos compartidos", ["data/processed/ (graph.npz, places_nodes.csv)     results/ (CSV, JSON, figuras)",
                                                     "Cada etapa guarda aquí sus resultados; la aplicación sale de estos archivos."], "store")
    arrow((2.9, 7.55), (4.1, 7.55), "red")
    arrow((2.9, 4.85), (4.1, 4.85), "lugares")
    arrow((7.3, 7.55), (8.8, 7.55), "grafo CSR")
    arrow((7.3, 4.85), (8.8, 4.85), "nodos UTM")
    arrow((11.8, 7.55), (13.1, 7.55), "matriz T")
    arrow((14.5, 2.3), (14.5, 3.7))
    ax.text(14.65, 3.0, "lee", fontsize=6.6, ha="left", va="center", color=INK)
    _save(fig, "arquitectura.png")


def all_figures():
    fig_r1(); fig_r2(); fig_r3(); fig_r4(); fig_itinerary(); fig_architecture()


if __name__ == "__main__":
    all_figures()
