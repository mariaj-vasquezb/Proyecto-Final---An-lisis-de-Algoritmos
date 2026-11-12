# Rutas del Paisaje Cultural Cafetero — Proyecto final

Red vial del Quindío, caminos mínimos (Dijkstra), envolvente convexa (Quickhull), viajante asimétrico (fuerza bruta, Held-Karp, voraz) y aplicación web.

> **Estado de los datos incluidos:** los resultados de `results/` y la aplicación `app/` se generaron con una **red vial sintética**
> (el entorno de preparación no tenía internet). Los algoritmos y mediciones son reales; los números no describen OpenStreetMap.
> El catálogo (`src/catalog.py`) tiene coordenadas aproximadas y fincas/acopios de ejemplo: **verifíquelos en un mapa**.

## Requisitos
Python 3.10+ y `pip install -r requirements.txt` (osmnx solo si usa datos reales).

## Reproducir
```bash
python -m unittest -v                                  # verificación de los algoritmos
python -m src.run_all --source synthetic --stage all   # red sintética (sin internet)
python -m src.run_all --source osm --stage all         # RED REAL (requiere internet y osmnx)
python -m src.plots                                    # figuras desde results/
python -m src.build_app                                # app/index.html
```
La etapa R4 con fuerza bruta tarda varios minutos (k=12 ≈ 3 min en la máquina de referencia). Etapas sueltas: `--stage r1|r2|r3|r4`.
Las etapas deben ejecutarse en orden (R1 genera el grafo; R2 la matriz; R4 usa la matriz).

## Estructura
`src/` código · `tests/` pruebas · `specs/` especificaciones (SDD) · `data/processed/` grafo y lugares ·
`results/` CSV/JSON y `figures/` · `app/index.html` aplicación (abrir en el navegador; `app/template.html` es su plantilla).

## Pendientes
1. Correr con `--source osm` y anotar la fecha de descarga; si falla, pedir el GraphML al docente.
2. Verificar coordenadas, reemplazar fincas/acopios de ejemplo y justificar duraciones de visita.
3. Comprobar en el código de su OSMnx qué hace `largest_component` (aquí se usó una réplica con NetworkX).
4. Medir todo en la misma máquina y reportar sus especificaciones.
