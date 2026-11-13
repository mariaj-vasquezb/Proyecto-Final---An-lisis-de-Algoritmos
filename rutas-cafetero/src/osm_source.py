"""Fuente de datos REAL: OpenStreetMap vía OSMnx. Requiere internet y `pip install osmnx`.

NOTA: este módulo NO pudo ejecutarse en el entorno donde se preparó el borrador (sin acceso a la red);
sigue la API documentada de OSMnx 2.x. Si algo falla, el mensaje de error indica la línea; los nombres de
funciones a revisar son ox.graph_from_place, ox.graph_from_point y ox.truncate.largest_component."""
import datetime
import numpy as np
from .model import parse_maxspeed

PLACE = "Quindío, Colombia"
ARMENIA_CENTER = (4.5339, -75.6811)      # plaza de Bolívar (lat, lon)


def raw_from_osmnx(G):
    """MultiDiGraph de OSMnx -> dict 'raw' (mismo formato que src.synth.generate)."""
    nodes = list(G.nodes)
    index = {n: i for i, n in enumerate(nodes)}
    u, v, length, hw, ms = [], [], [], [], []
    for a, b, d in G.edges(data=True):
        u.append(index[a]); v.append(index[b])
        length.append(float(d["length"]))
        hw.append(d.get("highway", "unclassified"))
        ms.append(parse_maxspeed(d.get("maxspeed")))
    return {"node_ids": np.array(nodes, dtype=np.int64),
            "lat": np.array([G.nodes[n]["y"] for n in nodes]),
            "lon": np.array([G.nodes[n]["x"] for n in nodes]),
            "u": np.array(u), "v": np.array(v), "length": np.array(length),
            "highway": hw, "maxspeed": np.array(ms)}


def download_department():
    import osmnx as ox
    G = ox.graph_from_place(PLACE, network_type="drive")
    return raw_from_osmnx(G), datetime.date.today().isoformat()


def download_radius(km):
    import osmnx as ox
    G = ox.graph_from_point(ARMENIA_CENTER, dist=km * 1000, dist_type="bbox", network_type="drive")
    return raw_from_osmnx(G)
