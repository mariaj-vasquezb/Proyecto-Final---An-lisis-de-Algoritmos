"""R1. Modelo de la red vial: pesos, componente fuertemente conexa, grafo CSR y asociación de lugares."""
import json
import numpy as np
import networkx as nx
from .geo import to_utm

# Velocidades por defecto (km/h) por tipo de vía, cuando no hay estadística local para imputar.
DEFAULT_KMH = {"motorway": 80, "trunk": 70, "primary": 60, "secondary": 50, "tertiary": 40,
               "unclassified": 30, "residential": 30, "living_street": 15, "service": 20, "track": 20, "path": 10}
MIN_KMH = 5.0


# ----------------------------------------------------------------------------- velocidades y pesos
def parse_maxspeed(v):
    """'50' -> 50; '30 mph' -> 48.3; lista -> primer valor válido; otro -> nan."""
    if isinstance(v, (list, tuple)):
        for x in v:
            r = parse_maxspeed(x)
            if not np.isnan(r):
                return r
        return float("nan")
    if v is None:
        return float("nan")
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower()
    try:
        num = float(s.split()[0])
    except (ValueError, IndexError):
        return float("nan")
    return num * 1.609344 if "mph" in s else num


def edge_speeds(highway, maxspeed):
    """Velocidad (km/h) de cada tramo. Orden de preferencia:
    1) maxspeed etiquetado; 2) media de los tramos etiquetados del mismo tipo de vía; 3) tabla por defecto.
    Devuelve (velocidades, origen) con origen 0=etiqueta, 1=media del tipo, 2=tabla."""
    hw = np.array([h[0] if isinstance(h, (list, tuple)) else h for h in highway])
    sp = np.asarray(maxspeed, float).copy()
    src = np.where(np.isnan(sp), 2, 0)
    for t in np.unique(hw):
        m = hw == t
        known = sp[m & ~np.isnan(sp)]
        miss = m & np.isnan(sp)
        if known.size:
            sp[miss] = known.mean(); src[miss] = 1
        else:
            sp[miss] = DEFAULT_KMH.get(t.replace("_link", ""), 30); src[miss] = 2
    return np.maximum(sp, MIN_KMH), src


# ----------------------------------------------------------------------------- componente fuertemente conexa
def to_networkx(raw):
    G = nx.MultiDiGraph()
    G.add_nodes_from(range(len(raw["node_ids"])))
    G.add_edges_from(zip(raw["u"].tolist(), raw["v"].tolist()))
    return G


def largest_component(G, strongly=True):
    """ox.truncate.largest_component si OSMnx está instalado; si no, réplica de su lógica:
    si el grafo no es (fuertemente) conexo, toma max(componentes, key=len) y induce el subgrafo.
    OSMnx usa nx.strongly_connected_components (Tarjan con la modificación de Nuutila; no recursivo), O(V+E)."""
    try:
        import osmnx as ox
        return ox.truncate.largest_component(G, strongly=strongly), "osmnx"
    except Exception:
        comps = nx.strongly_connected_components if strongly else nx.connected_components
        is_conn = nx.is_strongly_connected if strongly else nx.is_connected
        if not is_conn(G):
            keep = max(comps(G), key=len)
            G = nx.MultiDiGraph(G.subgraph(keep))
        return G, "networkx(réplica)"


# ----------------------------------------------------------------------------- grafo CSR
class RoadGraph:
    """Grafo dirigido en formato CSR (listas de adyacencia compactas)."""
    def __init__(self, ids, lat, lon, x, y, indptr, indices, dist, time):
        self.ids, self.lat, self.lon, self.x, self.y = ids, lat, lon, x, y
        self.indptr, self.indices, self.dist, self.time = indptr, indices, dist, time
        self.V, self.E = len(ids), len(indices)
        self._lists = None

    @property
    def lists(self):
        """(indptr, indices, time) como listas de Python: más rápido que NumPy dentro de bucles escalares."""
        if self._lists is None:
            self._lists = (self.indptr.tolist(), self.indices.tolist(), self.time.tolist())
        return self._lists

    def save(self, path):
        np.savez_compressed(path, ids=self.ids, lat=self.lat, lon=self.lon, x=self.x, y=self.y,
                            indptr=self.indptr, indices=self.indices, dist=self.dist, time=self.time)

    @classmethod
    def load(cls, path):
        d = np.load(path)
        return cls(*(d[k] for k in ["ids", "lat", "lon", "x", "y", "indptr", "indices", "dist", "time"]))


def build_graph(raw, strongly=True):
    """raw -> (RoadGraph de la componente, estadísticas). Pesos: distancia (m) y tiempo (s) = dist / v."""
    V0, E0 = len(raw["node_ids"]), len(raw["u"])
    speed, src = edge_speeds(raw["highway"], raw["maxspeed"])
    G = to_networkx(raw)
    H, impl = largest_component(G, strongly)
    keep_nodes = np.zeros(V0, bool)
    keep_nodes[np.fromiter(H.nodes, dtype=np.int64)] = True
    m = keep_nodes[raw["u"]] & keep_nodes[raw["v"]] & (raw["u"] != raw["v"])
    remap = -np.ones(V0, np.int64); remap[keep_nodes] = np.arange(keep_nodes.sum())
    u, v = remap[raw["u"][m]], remap[raw["v"][m]]
    dist = raw["length"][m]; tm = dist / (speed[m] / 3.6)
    # aristas paralelas: se conserva la de menor tiempo
    order = np.lexsort((tm, v, u)); u, v, dist, tm = u[order], v[order], dist[order], tm[order]
    first = np.ones(len(u), bool); first[1:] = (u[1:] != u[:-1]) | (v[1:] != v[:-1])
    u, v, dist, tm = u[first], v[first], dist[first], tm[first]
    n = int(keep_nodes.sum())
    indptr = np.zeros(n + 1, np.int64); np.add.at(indptr, u + 1, 1); indptr = np.cumsum(indptr)
    lat, lon = raw["lat"][keep_nodes], raw["lon"][keep_nodes]
    x, y = to_utm(lat, lon)
    g = RoadGraph(raw["node_ids"][keep_nodes], lat, lon, x, y, indptr, v.astype(np.int32),
                  dist.astype(np.float32), tm.astype(np.float64))
    stats = {"V_descargada": V0, "E_descargada": E0, "V_componente": g.V, "E_componente": g.E,
             "implementacion_scc": impl,
             "tramos_con_maxspeed_pct": round(100 * float((src == 0).mean()), 2),
             "tramos_imputados_media_tipo_pct": round(100 * float((src == 1).mean()), 2),
             "tramos_tabla_defecto_pct": round(100 * float((src == 2).mean()), 2),
             "velocidad_media_kmh": round(float(speed.mean()), 2)}
    return g, stats


# ----------------------------------------------------------------------------- lugares
def associate_places(g, places):
    """Nodo más cercano (distancia euclidiana en UTM 18N) a cada lugar. Devuelve nodo y distancia en m."""
    px, py = to_utm([p["lat"] for p in places], [p["lon"] for p in places])
    d2 = (g.x[None, :] - px[:, None]) ** 2 + (g.y[None, :] - py[:, None]) ** 2
    node = d2.argmin(axis=1)
    dist = np.sqrt(d2[np.arange(len(places)), node])
    return node, dist


def memory_estimates(V, E, cell_bytes=4, entry_bytes=12, offset_bytes=4):
    """MB de la matriz de adyacencia (V² celdas) y de las listas de adyacencia (CSR: E entradas + V+1 offsets)."""
    mb = 1024 ** 2
    return {"V": V, "E": E, "densidad_pct": 100 * E / (V * V),
            "matriz_MB": V * V * cell_bytes / mb,
            "listas_MB": (E * entry_bytes + (V + 1) * offset_bytes) / mb,
            "supuestos": f"matriz: {cell_bytes} B/celda (un peso float32); listas: {entry_bytes} B/entrada "
                         f"(destino int32 + distancia float32 + tiempo float32) + {offset_bytes} B/offset por nodo"}
