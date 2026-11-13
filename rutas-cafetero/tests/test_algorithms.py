"""Verificación de los algoritmos propios (protocolo experimental, punto 6). Ejecutar: python -m unittest -v"""
import random
import unittest
import numpy as np
import networkx as nx
from scipy.spatial import ConvexHull

from src.geo import to_utm, from_utm
from src.synth import generate, subset_bbox
from src.model import build_graph, parse_maxspeed, edge_speeds
from src.shortest import dijkstra_linear, dijkstra_heap
from src.hull import quickhull, cross, polygon_area2
from src.tsp import brute_force, held_karp, nearest_neighbor, sub_matrix, tour_cost


class TestGeo(unittest.TestCase):
    def test_roundtrip(self):
        la, lo = np.array([4.2, 4.53, 4.75]), np.array([-75.85, -75.68, -75.45])
        e, n = to_utm(la, lo)
        la2, lo2 = from_utm(e, n)
        self.assertLess(np.abs(la - la2).max(), 1e-6)
        self.assertLess(np.abs(lo - lo2).max(), 1e-6)

    def test_pyproj_if_available(self):
        try:
            from pyproj import Transformer
        except ImportError:
            self.skipTest("pyproj no instalado")
        t = Transformer.from_crs(4326, 32618, always_xy=True)
        e, n = t.transform(-75.6811, 4.5339)
        e2, n2 = to_utm(4.5339, -75.6811)
        self.assertLess(abs(e - e2) + abs(n - n2), 0.2)


class TestSpeeds(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_maxspeed("50"), 50)
        self.assertAlmostEqual(parse_maxspeed("30 mph"), 48.28032)
        self.assertEqual(parse_maxspeed(["none", "40"]), 40)
        self.assertTrue(np.isnan(parse_maxspeed(None)))

    def test_imputation(self):
        sp, src = edge_speeds(["a", "a", "a", "b"], [40.0, np.nan, 60.0, np.nan])
        self.assertEqual(sp[1], 50.0); self.assertEqual(src[1], 1)   # media del tipo
        self.assertEqual(src[3], 2)                                  # tabla por defecto


class TestDijkstra(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = subset_bbox(generate(), to_utm(4.5339, -75.6811), 6000)
        cls.g, _ = build_graph(raw)
        cls.lists = cls.g.lists
        G = nx.DiGraph()
        for u in range(cls.g.V):
            for k in range(cls.g.indptr[u], cls.g.indptr[u + 1]):
                G.add_edge(u, int(cls.g.indices[k]), weight=float(cls.g.time[k]))
        cls.G = G

    def test_hand_case(self):
        # 0->1 (1), 1->2 (1), 0->2 (5), 2->0 (1): camino mínimo 0->2 = 2 por 1
        lists = ([0, 2, 3, 4], [1, 2, 2, 0], [1.0, 5.0, 1.0, 1.0])
        for f in (dijkstra_linear, dijkstra_heap):
            r = f(lists, 3, 0, 2)
            self.assertEqual(r.time, 2.0); self.assertEqual(r.path, [0, 1, 2])
            self.assertEqual(f(lists, 3, 2, 1).time, 2.0)   # asimetría: 2->0->1

    def test_against_networkx_and_each_other(self):
        rng = random.Random(1)
        for _ in range(25):
            s, t = rng.randrange(self.g.V), rng.randrange(self.g.V)
            ref = nx.dijkstra_path_length(self.G, s, t)
            a = dijkstra_heap(self.lists, self.g.V, s, t)
            b = dijkstra_linear(self.lists, self.g.V, s, t)
            self.assertAlmostEqual(a.time, ref, places=6)
            self.assertAlmostEqual(b.time, ref, places=6)
            self.assertEqual(a.path[0], s); self.assertEqual(a.path[-1], t)
            # la ruta reconstruida suma el mismo tiempo
            tot = sum(self.G[u][v]["weight"] for u, v in zip(a.path, a.path[1:]))
            self.assertAlmostEqual(tot, ref, places=6)

    def test_sssp_matches(self):
        r = dijkstra_heap(self.lists, self.g.V, 0)
        ref = nx.single_source_dijkstra_path_length(self.G, 0)
        for v, d in ref.items():
            self.assertAlmostEqual(r.dist[v], d, places=6)


class TestHull(unittest.TestCase):
    def _same(self, pts):
        mine = quickhull(pts)
        arr = np.array(sorted(set(map(tuple, pts))), dtype=np.int64)
        ref = {tuple(p) for p in arr[ConvexHull(arr).vertices]}
        self.assertEqual(set(mine), ref)
        self.assertGreater(polygon_area2(mine), 0)               # antihorario
        n = len(mine)
        for i in range(n):                                        # giros estrictos: sin puntos alineados
            self.assertGreater(cross(mine[i], mine[(i + 1) % n], mine[(i + 2) % n]), 0)

    def test_random_with_collinear(self):
        rng = random.Random(3)
        for _ in range(300):
            m = rng.choice([3, 4, 6, 10])                        # rejilla pequeña => muchos alineados y repetidos
            pts = [(rng.randint(0, m), rng.randint(0, m)) for _ in range(rng.randint(5, 60))]
            if len({p for p in pts}) < 3 or len({p[0] for p in pts}) < 2 or len({p[1] for p in pts}) < 2:
                continue
            try:
                self._same(pts)
            except Exception as e:
                if "QH6154" in str(e) or "Initial simplex is flat" in str(e):
                    continue                                     # todos alineados: Qhull no aplica
                raise

    def test_large(self):
        rng = np.random.default_rng(5)
        pts = [tuple(p) for p in rng.integers(0, 100000, (20000, 2))]
        self._same(pts)


class TestTSP(unittest.TestCase):
    def test_hk_equals_brute(self):
        rng = random.Random(7)
        for k in range(2, 9):
            n = k + 1
            D = [[0 if i == j else rng.uniform(1, 100) for j in range(n)] for i in range(n)]   # asimétrica
            bf, bt = brute_force(D)
            hk, ht = held_karp(D)
            nn, nt = nearest_neighbor(D)
            self.assertAlmostEqual(bf, hk, places=9)
            self.assertAlmostEqual(tour_cost(D, ht), hk, places=9)
            self.assertEqual(sorted(ht[1:-1]), list(range(1, n)))
            self.assertEqual((ht[0], ht[-1]), (0, 0))
            self.assertGreaterEqual(nn, hk - 1e-9)

    def test_greedy_is_not_optimal_example(self):
        # 0->1 cuesta 1 (voraz lo elige) pero obliga a 1->2 = 100; el óptimo es 0->2->1->0
        D = [[0, 1, 2], [1, 0, 100], [2, 1, 0]]
        # voraz: 0->1->2->0 = 1 + 100 + 2 = 103 ; óptimo: 0->2->1->0 = 2 + 1 + 1 = 4
        self.assertEqual(nearest_neighbor(D)[0], 103)
        self.assertEqual(held_karp(D)[0], 4)

    def test_time_limit(self):
        n = 12
        D = [[0 if i == j else 1.0 + (i * 7 + j * 3) % 11 for j in range(n)] for i in range(n)]
        self.assertIsNone(brute_force(D, time_limit_s=0.0))


if __name__ == "__main__":
    unittest.main()
