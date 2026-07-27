"""
Shared fixtures and helpers for logsum tests.
All CSV construction is done programmatically via tmp_path — no static files needed.
"""
import csv

import pytest


def make_csv(path, rows, *, fieldnames=None):
    """Write a CSV to *path* from a list of dicts."""
    if fieldnames is None:
        fieldnames = ["timestamp", "level", "service", "message"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


# ── Input fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def happy_input(tmp_path):
    """Two services × two levels, clean timestamps, no edge cases."""
    p = tmp_path / "events.csv"
    make_csv(p, [
        {"timestamp": "2026-01-01T10:00:00", "level": "INFO",  "service": "checkout-service", "message": "placed"},
        {"timestamp": "2026-01-01T10:05:00", "level": "INFO",  "service": "checkout-service", "message": "confirmed"},
        {"timestamp": "2026-01-01T10:10:00", "level": "ERROR", "service": "checkout-service", "message": "failed"},
        {"timestamp": "2026-01-01T10:15:00", "level": "INFO",  "service": "cart-api",         "message": "created"},
        {"timestamp": "2026-01-01T10:20:00", "level": "ERROR", "service": "cart-api",         "message": "gone"},
        {"timestamp": "2026-01-01T10:25:00", "level": "ERROR", "service": "cart-api",         "message": "expired"},
    ])
    return p


@pytest.fixture
def padded_input(tmp_path):
    """level and service fields with surrounding whitespace."""
    p = tmp_path / "events.csv"
    make_csv(p, [
        {"timestamp": "2026-01-01T10:00:00", "level": " info ",  "service": "  checkout-service  ", "message": "a"},
        {"timestamp": "2026-01-01T10:05:00", "level": " ERROR ", "service": "  checkout-service  ", "message": "b"},
    ])
    return p


@pytest.fixture
def missing_level_input(tmp_path):
    """Two rows with empty level — both belong to (cart-api, UNKNOWN)."""
    p = tmp_path / "events.csv"
    make_csv(p, [
        {"timestamp": "2026-01-01T10:00:00", "level": "INFO", "service": "checkout-service", "message": "ok"},
        {"timestamp": "2026-01-01T10:05:00", "level": "",     "service": "cart-api",         "message": "no level"},
        {"timestamp": "2026-01-01T10:10:00", "level": "",     "service": "cart-api",         "message": "also missing"},
    ])
    return p


@pytest.fixture
def bad_ts_input(tmp_path):
    """Two rows with unparseable timestamps; one good row for checkout-service."""
    p = tmp_path / "events.csv"
    make_csv(p, [
        {"timestamp": "2026-01-01T10:00:00",  "level": "INFO",  "service": "checkout-service", "message": "good"},
        {"timestamp": "not-a-timestamp",       "level": "INFO",  "service": "cart-api",         "message": "bad"},
        {"timestamp": "2026-13-01T10:00:00",  "level": "ERROR", "service": "cart-api",         "message": "bad month"},
    ])
    return p


@pytest.fixture
def empty_input(tmp_path):
    """CSV with a header row and no data rows."""
    p = tmp_path / "events.csv"
    p.write_text("timestamp,level,service,message\n")
    return p
