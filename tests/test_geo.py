"""Tests for geo.py: WGS84 lat/lon -> UTM."""
import pytest

from geo import utm


def test_central_meridian_easting_is_500km():
    e, n = utm(64.0, -15.0, zone=28)
    assert e == pytest.approx(500_000, abs=0.01)


def test_equator_northing_is_zero():
    assert utm(0.0, -15.0, zone=28)[1] == pytest.approx(0, abs=0.01)


def test_northing_at_45_degrees():
    # Meridian arc to 45 deg on WGS84 is 4 984 944.4 m; UTM scales it by 0.9996.
    assert utm(45.0, -15.0, zone=28)[1] == pytest.approx(4_982_950.4, abs=0.5)

