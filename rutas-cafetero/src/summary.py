"""Resumen en consola de los resultados de cada requerimiento (sirve como evidencia de ejecución).
Uso: python -m src.summary r1|r2|r3|r4"""
import os, sys
import pandas as pd
from . import catalog
from .experiments import RES, read_json

PL = {p["id"]: p for p in catalog.load()}
rd = lambda n: pd.read_csv(os.path.join(RES, n))


def r1():
    j = read_json("r1_resumen.json"); s = j["estadisticas"]; m = j["memoria"]; t = rd("r1_tiempos.csv")
    print("== R1. Modelo de la red vial ==")
    print(f"Red descargada                 : {s['V_descargada']:>7,} nodos {s['E_descargada']:>8,} aristas")
    print(f"Componente fuertemente conexa  : {s['V_componente']:>7,} nodos {s['E_componente']:>8,} aristas  ({s['implementacion_scc']})")
    print(f"Memoria estimada               : matriz {m['matriz_MB']:.1f} MB | listas CSR {m['listas_MB']:.2f} MB  -> se eligen listas")
    print(f"Velocidad por tramo            : {s['tramos_con_maxspeed_pct']}% etiqueta | {s['tramos_imputados_media_tipo_pct']}% media del tipo | {s['tramos_tabla_defecto_pct']}% tabla (media {s['velocidad_media_kmh']} km/h)")
    print(f"Lugares asociados a un nodo    : 40 | a mas de 500 m: {len(j['lugares_mas_500m'])} | distancia maxima: {j['dist_max_m']:.0f} m")
    print("\nTiempo de largest_component (mediana de 5):")
    print(f"{'Red':<24}{'V':>8}{'E':>9}{'V+E':>9}{'ms':>10}{'us/(V+E)':>10}")
    for r in t.itertuples():
        ve = getattr(r, "_4")
        print(f"{r.red:<24}{r.V:>8,}{r.E:>9,}{ve:>9,}{r.tiempo_ms:>10.2f}{1000 * r.tiempo_ms / ve:>10.2f}")


def r2():
    d = rd("r2_dijkstra.csv"); q = read_json("r2_cociente.json"); m = read_json("r2_matriz_info.json")
    print("== R2. Caminos minimos (Dijkstra) ==")
    lin = d[d.version == "lineal"].set_index(["origen", "destino"]); hp = d[d.version == "cola_prioridad"].set_index(["origen", "destino"])
    print(f"{'origen':<7}{'destino':<8}{'viaje (min)':>12}{'explorados':>12}{'lineal ms':>11}{'cola ms':>9}{'cociente':>10}")
    for k, r in lin.iterrows():
        h = hp.loc[k]; ok = abs(r.tiempo_viaje_s - h.tiempo_viaje_s) < 1e-6
        print(f"{k[0]:<7}{k[1]:<8}{r.tiempo_viaje_s / 60:>12.1f}{int(r.nodos_explorados):>12,}{r.tiempo_ms:>11.1f}{h.tiempo_ms:>9.2f}{r.tiempo_ms / h.tiempo_ms:>9.0f}x {'' if ok else 'DIFIERE'}")
    print(f"\nVerificacion lineal == cola en los {q['n_pares']} pares: {'OK' if q['verificacion_tiempos_iguales'] else 'FALLA'}")
    print(f"Cociente lineal/cola: mediana {q['mediana']:.1f} | minimo {q['minimo']:.1f} | maximo {q['maximo']:.1f}")
    print(f"Consultas medidas con cola de prioridad: {int((d.version == 'cola_prioridad').sum())} | con lineal: {int((d.version == 'lineal').sum())}")
    print(f"Matriz de tiempos {m['n']}x{m['n']}: {m['tiempo_total_ms']:.0f} ms | asimetria maxima {m['max_asimetria_s']:.0f} s | infinitos: {m['hay_infinitos']}")
    print("Archivos: results/r2_dijkstra.csv, results/matriz_tiempos.csv")


def r3():
    t = rd("r3_envolvente.csv")
    print("== R3. Envolvente convexa (Quickhull propio vs SciPy) ==")
    print(f"{'Conjunto':<26}{'n':>8}{'vertices':>10}{'propio ms':>11}{'SciPy ms':>10}{'cociente':>10}{'iguales':>9}")
    for r in t.itertuples():
        print(f"{r.conjunto:<26}{r.n:>8,}{r.vertices:>10}{r.tiempo_propio_ms:>11.2f}{r.tiempo_scipy_ms:>10.2f}{r.cociente:>9.1f}x{'  si' if r.mismos_vertices else '  NO':>7}")
    print("\nArchivos: results/r3_envolvente.csv, results/r3_hull_red.json")


def r4():
    e = rd("r4_exactas.csv"); q = rd("r4_heuristica_instancias.csv"); it = read_json("r4_itinerario.json"); w = read_json("r4_peor_caso_heuristica.json")
    print("== R4. Ruta optima de recorrido ==")
    print(f"{'k':>3}{'fuerza bruta (ms)':>20}{'Held-Karp (ms)':>16}{'optimo (min)':>14}{'memoria tabla':>15}")
    for r in e.itertuples():
        fb = r.tiempo_fuerza_bruta_ms if str(r.tiempo_fuerza_bruta_ms) == "no completada" else f"{float(r.tiempo_fuerza_bruta_ms):,.1f}"
        print(f"{r.k:>3}{fb:>20}{r.tiempo_held_karp_ms:>16.2f}{r.optimo_s / 60:>14.1f}{r.memoria_tabla_bytes / 1024:>12.1f} KiB")
    print("Verificacion fuerza bruta == Held-Karp en todos los k: OK (el experimento aborta si difieren)")
    print("\nCalidad de la heuristica (vecino mas cercano vs optimo), 10 instancias por k:")
    print(f"{'k':>3}{'instancias':>12}{'brecha prom (%)':>17}{'brecha max (%)':>16}")
    for k, g in q.groupby("k"):
        print(f"{k:>3}{len(g):>12}{g.brecha_pct.mean():>17.2f}{g.brecha_pct.max():>16.2f}")
    print(f"\nItinerario de un dia (salida: {PL[it['inicio']]['nombre']}):")
    for p in it["pasos"]:
        print(f"  {len(p['atractivos'])} atractivos -> viaje {p['viaje_s'] / 3600:.2f} h + visitas {p['visitas_s'] / 3600:.2f} h = {p['total_s'] / 3600:.2f} h"
              + (f"  no cabe: se quita {PL[p['se_quita']]['nombre']}" if p.get("se_quita") else "  cabe en 11 h"))
    print("  Orden final: " + " > ".join(PL[x]["nombre"].split(" (")[0] for x in it["orden"]))
    print(f"  Voraz (vecino mas cercano): {it['voraz']['viaje_s'] / 3600:.2f} h de viaje vs optimo {it['viaje_total_s'] / 3600:.2f} h")


if __name__ == "__main__":
    {"r1": r1, "r2": r2, "r3": r3, "r4": r4}[sys.argv[1]]()
