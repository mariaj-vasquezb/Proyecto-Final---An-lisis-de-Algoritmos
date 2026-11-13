"""R3. Envolvente convexa por divide y vencerás (Quickhull) con aritmética entera exacta.

Recurrencia: T(n) = T(n1) + T(n2) + O(n), con n1 + n2 <= n - 1 (el punto más lejano c se descarta y los puntos
dentro del triángulo (a, c, b) también). Mejor/caso medio con particiones balanceadas: O(n log n); peor caso
(particiones muy desiguales): O(n²). Si h es el número de vértices, el caso medio con puntos uniformes es
cercano a O(n log h) porque la mayoría de los puntos se descarta pronto.
Los puntos alineados sobre un lado NO se cuentan como vértices (se usa cruz estrictamente < 0)."""
import sys

sys.setrecursionlimit(10000)


def cross(o, a, b):
    """Producto cruz (a-o) x (b-o). > 0: giro antihorario; 0: alineados. Enteros de Python (sin desbordamiento)."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _chain(a, b, pts):
    """Vértices estrictamente entre a y b que están a la DERECHA de a->b, en el orden del recorrido."""
    if not pts:
        return []
    c, cmin = None, 0
    for p in pts:                                # divide: el punto más lejano de la recta a-b es vértice seguro
        v = cross(a, b, p)
        if v < cmin:
            cmin, c = v, p
    right_ac = [p for p in pts if cross(a, c, p) < 0]
    right_cb = [p for p in pts if cross(c, b, p) < 0]
    return _chain(a, c, right_ac) + [c] + _chain(c, b, right_cb)   # combina


def quickhull(points):
    """Vértices de la envolvente en sentido antihorario empezando por el punto más a la izquierda."""
    pts = sorted(set(map(tuple, points)))
    if len(pts) <= 2:
        return pts
    l, r = pts[0], pts[-1]
    inner = pts[1:-1]
    lower = [p for p in inner if cross(l, r, p) < 0]     # a la derecha de l->r (debajo)
    upper = [p for p in inner if cross(l, r, p) > 0]     # a la izquierda de l->r (encima)
    hull = [l] + _chain(l, r, lower) + [r] + _chain(r, l, upper)
    return hull


def polygon_area2(h):
    """Dos veces el área con signo (fórmula del cordón): positiva si el polígono es antihorario."""
    return sum(h[i][0] * h[(i + 1) % len(h)][1] - h[(i + 1) % len(h)][0] * h[i][1] for i in range(len(h)))
