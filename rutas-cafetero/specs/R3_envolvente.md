# Spec R3 — Envolvente convexa
- Coordenadas UTM 18N redondeadas a enteros, sin repetidos; cruz con enteros; alineados NO son vértices.
- Quickhull (divide y vencerás) propio; salida antihoraria desde el punto más a la izquierda.
- Experimento: nodos de la red + cuadrado de 1 000, 10 000, 50 000 puntos (semilla 42) vs scipy.spatial.ConvexHull.
## Pruebas
- Mismos vértices que SciPy en rejillas pequeñas con muchos alineados y repetidos, en 20 000 puntos y en los 4 conjuntos. Giros estrictamente positivos.
