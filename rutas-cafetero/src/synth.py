"""Red vial SINTÉTICA del Quindío (sustituto de OSM cuando no hay internet).

NO es OpenStreetMap: es una cuadrícula perturbada, con jerarquía de vías, tramos de un solo sentido, vías
sin velocidad etiquetada y callejones sin salida, recortada a un contorno ilustrativo del departamento.
Sirve para ejecutar y medir los algoritmos de punta a punta. Con internet, `--source osm` la reemplaza."""
import numpy as np
from matplotlib.path import Path
from .geo import to_utm, from_utm

# Contorno ILUSTRATIVO (lon, lat), no es el límite oficial del departamento.
MASK_LONLAT = [(-75.88, 4.62), (-75.82, 4.74), (-75.70, 4.76), (-75.60, 4.72), (-75.52, 4.70), (-75.44, 4.66),
               (-75.42, 4.58), (-75.50, 4.50), (-75.56, 4.42), (-75.62, 4.30), (-75.66, 4.20), (-75.72, 4.14),
               (-75.80, 4.12), (-75.86, 4.20), (-75.82, 4.30), (-75.84, 4.40), (-75.80, 4.48), (-75.86, 4.55)]

# clase: (prob. de existir, velocidad km/h, prob. de tener maxspeed etiquetado, prob. de sentido único, sinuosidad)
CLASSES = {
    "primary": (1.00, 60, 0.90, 0.00, (1.02, 1.15)),
    "secondary": (0.97, 50, 0.60, 0.00, (1.05, 1.25)),
    "tertiary": (0.85, 40, 0.25, 0.05, (1.10, 1.35)),
    "residential": (0.75, 30, 0.05, 0.12, (1.05, 1.30)),
    "unclassified": (0.70, 30, 0.00, 0.10, (1.10, 1.40)),
    "track": (0.60, 20, 0.00, 0.00, (1.20, 1.50)),
}
MINOR = ["tertiary", "residential", "unclassified", "track"]
MINOR_P = [0.30, 0.40, 0.20, 0.10]


def generate(seed=7, step=450.0):
    """Devuelve un dict 'raw': node_ids, lat, lon, edges (u, v, length, highway, maxspeed)."""
    rng = np.random.default_rng(seed)
    xa, ya = to_utm(4.08, -75.90)
    xb, yb = to_utm(4.80, -75.40)
    xs, ys = np.arange(float(xa), float(xb), step), np.arange(float(ya), float(yb), step)
    nxn, nyn = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    X = X + rng.uniform(-0.25, 0.25, X.shape) * step
    Y = Y + rng.uniform(-0.25, 0.25, Y.shape) * step
    lat, lon = from_utm(X.ravel(), Y.ravel())
    inside = Path(MASK_LONLAT).contains_points(np.c_[lon, lat])
    gid = -np.ones(nxn * nyn, dtype=np.int64)
    gid[inside] = np.arange(inside.sum())
    Xf, Yf = X.ravel(), Y.ravel()
    U, V, L, H, S = [], [], [], [], []

    def add(a, b, cls):
        keep, spd, ptag, p1, (s0, s1) = CLASSES[cls]
        if rng.random() > keep:
            return
        length = float(np.hypot(Xf[a] - Xf[b], Yf[a] - Yf[b]) * rng.uniform(s0, s1))
        tag = float(spd) if rng.random() < ptag else np.nan
        pairs = [(a, b), (b, a)]
        if rng.random() < p1:
            pairs = [pairs[rng.integers(2)]]
        for u, v in pairs:
            U.append(u); V.append(v); L.append(length); H.append(cls); S.append(tag)

    def cls_of(line):
        if line % 24 == 0:
            return "primary"
        if line % 8 == 0:
            return "secondary"
        return str(rng.choice(MINOR, p=MINOR_P))

    for i in range(nxn):
        for j in range(nyn):
            a = i * nyn + j
            if gid[a] < 0:
                continue
            if i + 1 < nxn and gid[a + nyn] >= 0:       # hacia el este (fila j)
                add(a, a + nyn, cls_of(j))
            if j + 1 < nyn and gid[a + 1] >= 0:         # hacia el norte (columna i)
                add(a, a + 1, cls_of(i))
    U, V = np.array(U), np.array(V)
    used = np.unique(np.concatenate([U, V]))             # elimina nodos aislados
    remap = -np.ones(nxn * nyn, dtype=np.int64)
    remap[used] = np.arange(len(used))
    return {
        "node_ids": 1_000_000 + used.astype(np.int64) * 7,   # ids con aspecto de OSM
        "lat": lat[used], "lon": lon[used],
        "u": remap[U], "v": remap[V],
        "length": np.array(L), "highway": H, "maxspeed": np.array(S),
    }


def subset_bbox(raw, center_xy, half_side_m):
    """Equivalente a ox.graph_from_point(..., dist=half_side, dist_type='bbox'): nodos dentro de un cuadrado."""
    x, y = to_utm(raw["lat"], raw["lon"])
    keep = (np.abs(x - center_xy[0]) <= half_side_m) & (np.abs(y - center_xy[1]) <= half_side_m)
    return subset_nodes(raw, keep)


def subset_nodes(raw, keep):
    remap = -np.ones(len(keep), dtype=np.int64)
    remap[keep] = np.arange(keep.sum())
    m = keep[raw["u"]] & keep[raw["v"]]
    return {"node_ids": raw["node_ids"][keep], "lat": raw["lat"][keep], "lon": raw["lon"][keep],
            "u": remap[raw["u"][m]], "v": remap[raw["v"][m]], "length": raw["length"][m],
            "highway": [h for h, k in zip(raw["highway"], m) if k], "maxspeed": raw["maxspeed"][m]}
