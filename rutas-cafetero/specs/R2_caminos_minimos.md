# Spec R2 — Caminos mínimos
- dijkstra_linear O(V²) y dijkstra_heap O((V+E) log V): se detienen al sacar el destino; devuelven tiempo, ruta y nodos explorados (contados al salir de la cola por primera vez). Sin destino: árbol completo.
- Medición: 20 pares con cola; 10 pares cercanos con ambas versiones; mediana de 5 repeticiones.
- Matriz 40×40 con cola, una corrida por lugar; CSV con ids en fila y columna superior.
## Pruebas
- Grafo de 3 nodos resuelto a mano (incluye asimetría). 25 pares aleatorios = NetworkX. Suma de pesos de la ruta = tiempo. Lineal = cola en todos los pares medidos.
