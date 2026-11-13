"""R4. Viajante asimétrico: fuerza bruta, Held-Karp (programación dinámica) y heurística voraz (vecino más cercano).

Todas reciben una matriz local D de (k+1)x(k+1) con la salida/llegada en el índice 0 y los k lugares a visitar
en 1..k. Devuelven (costo, recorrido) con el recorrido como lista de índices que empieza y termina en 0.

Held-Karp. Subestructura óptima: sea f(S, j) el menor tiempo para salir de 0, visitar exactamente el conjunto
S de lugares y terminar en j (j en S). Si el recorrido óptimo termina en j, el tramo que llega a i (el penúltimo)
debe ser óptimo para (S \\ {j}, i); si no, se sustituye por uno mejor y se mejora el total (argumento de corte y
pegado). Recurrencia:
    f({j}, j) = D[0][j]
    f(S, j)   = min_{i in S\\{j}} f(S\\{j}, i) + D[i][j]
    óptimo    = min_j f(todos, j) + D[j][0]
Hay 2^k·k estados y cada uno cuesta O(k): tiempo O(2^k·k²), memoria O(2^k·k)."""
from itertools import permutations
from time import perf_counter

INF = float("inf")


def sub_matrix(M, ids):
    """Submatriz de M (lista de listas) para los lugares ids (ids[0] = salida)."""
    return [[M[a][b] for b in ids] for a in ids]


def tour_cost(D, tour):
    return sum(D[tour[i]][tour[i + 1]] for i in range(len(tour) - 1))


def brute_force(D, time_limit_s=None):
    """Prueba las k! permutaciones. Devuelve None si supera el límite de tiempo ('no completada')."""
    k = len(D) - 1
    row0 = D[0]
    best, best_p = INF, None
    t0 = perf_counter()
    n = 0
    for p in permutations(range(1, k + 1)):
        c = row0[p[0]]
        a = p[0]
        for b in p[1:]:
            c += D[a][b]
            a = b
        c += D[a][0]
        if c < best:
            best, best_p = c, p
        n += 1
        if time_limit_s is not None and (n & 0xFFFF) == 0 and perf_counter() - t0 > time_limit_s:
            return None
    return best, [0, *best_p, 0]


def held_karp(D):
    k = len(D) - 1
    full = (1 << k) - 1
    dp = [[INF] * k for _ in range(1 << k)]
    par = [[-1] * k for _ in range(1 << k)]
    for j in range(k):
        dp[1 << j][j] = D[0][j + 1]
    for mask in range(1, 1 << k):
        row = dp[mask]
        for j in range(k):
            cur = row[j]
            if cur == INF:
                continue
            Dj = D[j + 1]
            for n in range(k):
                bit = 1 << n
                if mask & bit:
                    continue
                nm = mask | bit
                c = cur + Dj[n + 1]
                if c < dp[nm][n]:
                    dp[nm][n] = c; par[nm][n] = j
    best, last = INF, -1
    for j in range(k):
        c = dp[full][j] + D[j + 1][0]
        if c < best:
            best, last = c, j
    order, mask, j = [], full, last                # reconstruye el recorrido hacia atrás
    while j != -1:
        order.append(j + 1)
        pj = par[mask][j]
        mask ^= 1 << j
        j = pj
    return best, [0, *order[::-1], 0]


def held_karp_memory_bytes(k, cell_bytes=8, parent_bytes=1):
    """Memoria teórica de la tabla: 2^k · k celdas de costo (+ predecesor)."""
    return (1 << k) * k * (cell_bytes + parent_bytes)


def nearest_neighbor(D):
    """Voraz: desde la salida, ir siempre al lugar no visitado con menor tiempo desde el actual; luego regresar. O(k²)."""
    k = len(D) - 1
    left = set(range(1, k + 1))
    cur, tour = 0, [0]
    while left:
        nxt = min(left, key=lambda j: D[cur][j])
        left.remove(nxt); tour.append(nxt); cur = nxt
    tour.append(0)
    return tour_cost(D, tour), tour
