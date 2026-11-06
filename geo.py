"""WGS84 latitude/longitude -> UTM easting/northing, in plain Python.

Used by make_model.py to place the cave marker on the ODM model, whose
coordinates are UTM 28N metres minus a fixed offset. Krüger's series to
the 4th order: millimetre-accurate within a UTM zone.
"""
import math

A = 6_378_137.0                 # WGS84 semi-major axis, m
F = 1 / 298.257223563           # WGS84 flattening
K0 = 0.9996                     # UTM scale on the central meridian


def utm(lat: float, lon: float, zone: int) -> tuple[float, float]:
    """(easting, northing) in metres, northern hemisphere, for a given zone."""
    n = F / (2 - F)
    a_hat = A / (1 + n) * (1 + n**2 / 4 + n**4 / 64)
    alpha = (n / 2 - 2 * n**2 / 3 + 5 * n**3 / 16,
             13 * n**2 / 48 - 3 * n**3 / 5,
             61 * n**3 / 240)
    phi = math.radians(lat)
    dlam = math.radians(lon - (zone * 6 - 183))
    e = 2 * math.sqrt(n) / (1 + n)
    t = math.sinh(math.atanh(math.sin(phi)) - e * math.atanh(e * math.sin(phi)))
    xi = math.atan2(t, math.cos(dlam))
    eta = math.atanh(math.sin(dlam) / math.sqrt(1 + t * t))
    x = eta + sum(a * math.cos(2 * j * xi) * math.sinh(2 * j * eta) for j, a in enumerate(alpha, 1))
    y = xi + sum(a * math.sin(2 * j * xi) * math.cosh(2 * j * eta) for j, a in enumerate(alpha, 1))
    return 500_000 + K0 * a_hat * x, K0 * a_hat * y
