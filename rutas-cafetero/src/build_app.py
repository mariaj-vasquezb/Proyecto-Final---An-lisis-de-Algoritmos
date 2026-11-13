"""R5. Genera app/index.html (un solo archivo, sin dependencias externas) con los datos de results/ y data/processed/.
Uso: python -m src.build_app"""
import base64, json, os
import numpy as np
import pandas as pd

from . import catalog
from .experiments import ROOT, RES, load_graph, load_matrix, read_json

FIGS = ["arquitectura", "r1_escalamiento", "r2_dijkstra", "r3_envolvente_mapa", "r3_tiempos",
        "r4_exactas", "r4_heuristica", "r4_itinerario_mapa"]


def build():
    g, places = load_graph()
    env = read_json("environment.json")
    synthetic = env["fuente_datos"] == "synthetic"
    ids, M = load_matrix()
    x0, y0 = float(g.x.min()), float(g.y.min())
    hull = read_json("r3_hull_red.json")["utm"]
    r4 = pd.read_csv(os.path.join(RES, "r4_exactas.csv"))
    q = pd.read_csv(os.path.join(RES, "r4_heuristica_instancias.csv"))
    it = read_json("r4_itinerario.json")
    banner = ("<b>Datos de demostración:</b> red vial <b>sintética</b> (no es OpenStreetMap), generada porque el entorno de "
              "preparación no tenía internet. Los algoritmos y las mediciones son reales; para usar la red real ejecute "
              "<code>python -m src.run_all --source osm</code> y luego <code>python -m src.build_app</code>. "
              "Coordenadas y duraciones del catálogo: aproximadas, por verificar."
              if synthetic else
              "Red vial de OpenStreetMap (descargada con OSMnx). Estimaciones del modelo, no tiempos reales de recorrido.")
    data = {
        "meta": {"banner": banner},
        "defaults": {"start": catalog.START_ID, "itin_attr": []},
        "x": np.round(g.x - x0).astype(int).tolist(), "y": np.round(g.y - y0).astype(int).tolist(),
        "indptr": g.indptr.tolist(), "indices": g.indices.tolist(),
        "time": np.round(g.time, 2).tolist(), "dist": np.round(g.dist).astype(int).tolist(),
        "places": [{"id": p["id"], "nombre": p["nombre"], "municipio": p["municipio"], "categoria": p["categoria"],
                    "node": p["node"], "visita_min": p["visita_min"]} for p in places],
        "matrix": [[round(v, 1) for v in r] for r in M],
        "hull": [[h[0] - x0, h[1] - y0] for h in hull],
        "env": env,
        "res": {
            "r1": read_json("r1_resumen.json"),
            "r1t": pd.read_csv(os.path.join(RES, "r1_tiempos.csv")).to_dict("records"),
            "r2q": read_json("r2_cociente.json"), "r2m": read_json("r2_matriz_info.json"),
            "r3": pd.read_csv(os.path.join(RES, "r3_envolvente.csv")).to_dict("records"),
            "r4": [{"k": int(r.k), "fb": (float(r.tiempo_fuerza_bruta_ms) if str(r.tiempo_fuerza_bruta_ms).replace('.', '', 1).isdigit()
                                          else str(r.tiempo_fuerza_bruta_ms)), "hk": float(r.tiempo_held_karp_ms)} for r in r4.itertuples()],
            "r4q": [{"k": int(k), "n": int(len(s)), "media": float(s.brecha_pct.mean()), "max": float(s.brecha_pct.max())}
                    for k, s in q.groupby("k")],
        },
        "figs": {},
    }
    # El itinerario por defecto de la app son los 8 atractivos de partida (se recalcula en el navegador)
    from .experiments import ITIN_ATTR
    data["defaults"]["itin_attr"] = ITIN_ATTR
    for name in FIGS:
        fp = os.path.join(RES, "figures", name + ".png")
        if os.path.exists(fp):
            data["figs"][name] = base64.b64encode(open(fp, "rb").read()).decode()
    tpl = open(os.path.join(ROOT, "app", "template.html"), encoding="utf-8").read()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = tpl.replace("/*__DATA__*/", blob)
    with open(os.path.join(ROOT, "app", "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print("app/index.html", round(len(out) / 1e6, 2), "MB")


if __name__ == "__main__":
    build()
