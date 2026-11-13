"""Punto de entrada: python -m src.run_all --source synthetic|osm --stage r1|r2|r3|r4|all"""
import argparse
from . import experiments as ex

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["synthetic", "osm"], default="osm")
    ap.add_argument("--stage", choices=["r1", "r2", "r3", "r4", "all"], default="all")
    a = ap.parse_args()
    if a.stage in ("r1", "all"): ex.run_r1(a.source)
    if a.stage in ("r2", "all"): ex.run_r2()
    if a.stage in ("r3", "all"): ex.run_r3()
    if a.stage in ("r4", "all"): ex.run_r4()
