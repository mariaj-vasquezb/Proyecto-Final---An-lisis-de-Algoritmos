# Spec R4 — Ruta óptima (ATSP)
- Fuerza bruta (límite 5 min -> "no completada"), Held-Karp con recorrido, vecino más cercano.
- k = 5..12 desde Armenia con k lugares al azar (semilla 1000+k). Calidad: k = 5, 8, 10, 12 con 10 instancias.
- Itinerario: 8 atractivos desde Armenia; si no caben en 11 h se quita el que más tiempo ahorra y se recalcula.
## Pruebas
- HK = fuerza bruta (k=2..8, matrices asimétricas); recorrido válido y costo recalculado igual; voraz ≥ óptimo.
- Ejemplo de 3 lugares donde el voraz da 103 y el óptimo 4. Límite de tiempo devuelve None.
