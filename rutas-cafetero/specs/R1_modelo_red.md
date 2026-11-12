# Spec R1 — Modelo de la red vial
**Entrada:** red OSM (o sintética) + catálogo de 40 lugares. **Salida:** data/processed/graph.npz, places_nodes.csv, results/r1_*.csv|json.
## Comportamiento
- Velocidad por tramo: maxspeed > media del tipo de vía > tabla por defecto; mínimo 5 km/h. tiempo_s = distancia_m / (v/3.6).
- Se conserva la componente fuertemente conexa más grande (ox.truncate.largest_component si hay OSMnx).
- Cada lugar -> nodo más cercano (distancia euclidiana UTM 18N). Se reportan los lugares a > 500 m.
- Se estima memoria de matriz vs listas con supuestos explícitos y se elige representación.
## Casos de prueba (tests/test_algorithms.py)
- parse_maxspeed("50")=50; "30 mph"≈48.28; ["none","40"]=40; None=nan.
- Imputación: tramo sin velocidad toma la media de su tipo; tipo sin etiquetas usa la tabla.
- Ida y vuelta UTM < 1e-6 grados. Todo par de nodos de la componente tiene ruta.
