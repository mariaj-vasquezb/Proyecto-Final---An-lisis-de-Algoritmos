"""R2. Dijkstra de implementación propia: versión lineal O(V²) y versión con cola de prioridad O((V+E) log V).

Convenciones (enunciado): se detienen al sacar el destino; devuelven tiempo, ruta (por predecesores) y nodos
explorados. Un nodo se cuenta como explorado una sola vez, la primera vez que sale de la cola.
Con destino=None calculan el árbol completo de caminos mínimos desde el origen (se usa para la matriz)."""
from heapq import heappush, heappop
from collections import namedtuple

INF = float("inf")
Result = namedtuple("Result", "time path explored dist")


def _path(prev, t):
    p = []
    while t != -1:
        p.append(t)
        t = prev[t]
    return p[::-1]


def dijkstra_linear(lists, V, s, t=None):
    """Extrae el mínimo recorriendo todos los nodos no visitados: V extracciones x O(V) = O(V²)."""
    ptr, idx, w = lists
    dist = [INF] * V; prev = [-1] * V; done = [False] * V
    dist[s] = 0.0
    explored = 0
    for _ in range(V):
        u, best = -1, INF
        for v in range(V):                       # búsqueda lineal del mínimo
            if not done[v] and dist[v] < best:
                best = dist[v]; u = v
        if u == -1:
            break                                # el resto es inalcanzable
        done[u] = True; explored += 1
        if u == t:
            return Result(best, _path(prev, t), explored, None)
        for k in range(ptr[u], ptr[u + 1]):
            v = idx[k]; nd = best + w[k]
            if nd < dist[v]:
                dist[v] = nd; prev[v] = u
    if t is None:
        return Result(None, None, explored, dist)
    return Result(INF, [], explored, None)


def dijkstra_heap(lists, V, s, t=None):
    """Cola de prioridad binaria (heapq) con eliminación perezosa: cada arista puede insertar una entrada."""
    ptr, idx, w = lists
    dist = [INF] * V; prev = [-1] * V; done = [False] * V
    dist[s] = 0.0
    heap = [(0.0, s)]
    explored = 0
    while heap:
        d, u = heappop(heap)
        if done[u]:
            continue                             # entrada obsoleta
        done[u] = True; explored += 1
        if u == t:
            return Result(d, _path(prev, t), explored, None)
        for k in range(ptr[u], ptr[u + 1]):
            v = idx[k]; nd = d + w[k]
            if nd < dist[v]:
                dist[v] = nd; prev[v] = u
                heappush(heap, (nd, v))
    if t is None:
        return Result(None, None, explored, dist)
    return Result(INF, [], explored, None)
