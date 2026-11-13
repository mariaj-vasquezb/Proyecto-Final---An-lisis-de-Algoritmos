"""Conversión WGS84 <-> UTM zona 18N (EPSG:32618), serie de Krüger de 3 términos (error < 10 cm en esta zona).
Se implementa a mano para no depender de pyproj; pyproj solo se usa en las pruebas si está instalado."""
import numpy as np

_A, _F, _K0 = 6378137.0, 1 / 298.257223563, 0.9996
_LON0 = np.radians(-75.0)          # meridiano central de la zona 18
_N = _F / (2 - _F)
_AH = _A / (1 + _N) * (1 + _N**2 / 4 + _N**4 / 64)
_ALPHA = [_N/2 - 2*_N**2/3 + 5*_N**3/16, 13*_N**2/48 - 3*_N**3/5, 61*_N**3/240]
_BETA = [_N/2 - 2*_N**2/3 + 37*_N**3/96, _N**2/48 + _N**3/15, 17*_N**3/480]
_DELTA = [2*_N - 2*_N**2/3 - 2*_N**3, 7*_N**2/3 - 8*_N**3/5, 56*_N**3/15]
_FE = 500000.0


def to_utm(lat, lon):
    """(lat, lon) en grados -> (este, norte) en metros."""
    phi = np.radians(np.asarray(lat, float))
    lam = np.radians(np.asarray(lon, float)) - _LON0
    q = 2 * np.sqrt(_N) / (1 + _N)
    t = np.sinh(np.arctanh(np.sin(phi)) - q * np.arctanh(q * np.sin(phi)))
    xi_p = np.arctan2(t, np.cos(lam))
    eta_p = np.arctanh(np.sin(lam) / np.sqrt(1 + t * t))
    xi, eta = xi_p.copy(), eta_p.copy()
    for j, a in enumerate(_ALPHA, 1):
        xi = xi + a * np.sin(2*j*xi_p) * np.cosh(2*j*eta_p)
        eta = eta + a * np.cos(2*j*xi_p) * np.sinh(2*j*eta_p)
    return _FE + _K0 * _AH * eta, _K0 * _AH * xi


def from_utm(e, n):
    """(este, norte) en metros -> (lat, lon) en grados."""
    xi = np.asarray(n, float) / (_K0 * _AH)
    eta = (np.asarray(e, float) - _FE) / (_K0 * _AH)
    xi_p, eta_p = xi.copy(), eta.copy()
    for j, b in enumerate(_BETA, 1):
        xi_p = xi_p - b * np.sin(2*j*xi) * np.cosh(2*j*eta)
        eta_p = eta_p - b * np.cos(2*j*xi) * np.sinh(2*j*eta)
    chi = np.arcsin(np.sin(xi_p) / np.cosh(eta_p))
    phi = chi.copy()
    for j, d in enumerate(_DELTA, 1):
        phi = phi + d * np.sin(2*j*chi)
    lam = _LON0 + np.arctan2(np.sinh(eta_p), np.cos(xi_p))
    return np.degrees(phi), np.degrees(lam)
