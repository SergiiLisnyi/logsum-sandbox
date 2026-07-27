"""
Pytest suite for logsum CLI — derived from spec.md only.
All tests invoke src/logsum.py as a subprocess; no source is read.
"""
import csv
import subprocess
import sys
from pathlib import Path

from conftest import make_csv

ENTRY = Path(__file__).parent.parent / "src" / "logsum.py"


# ── CLI + CSV helpers ─────────────────────────────────────────────────────────

def run_cli(*args):
    result = subprocess.run(
        [sys.executable, str(ENTRY), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def read_summary(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def read_header(path):
    with open(path, newline="") as f:
        return next(csv.reader(f))


# ── §1  Grouping ──────────────────────────────────────────────────────────────

class TestGrouping:
    def test_one_row_per_service_level_pair(self, tmp_path, happy_input):
        out = tmp_path / "summary.csv"
        rc, _, _ = run_cli("--input", str(happy_input), "--output", str(out))
        assert rc == 0
        keys = {(r["service"], r["level"]) for r in read_summary(out)}
        assert keys == {
            ("checkout-service", "INFO"),
            ("checkout-service", "ERROR"),
            ("cart-api", "INFO"),
            ("cart-api", "ERROR"),
        }

    def test_count_per_group(self, tmp_path, happy_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(happy_input), "--output", str(out))
        by_key = {(r["service"], r["level"]): int(r["count"]) for r in read_summary(out)}
        assert by_key[("checkout-service", "INFO")]  == 2
        assert by_key[("checkout-service", "ERROR")] == 1
        assert by_key[("cart-api", "INFO")]           == 1
        assert by_key[("cart-api", "ERROR")]          == 2

    def test_first_seen_is_minimum_timestamp_in_group(self, tmp_path, happy_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(happy_input), "--output", str(out))
        row = next(
            r for r in read_summary(out)
            if r["service"] == "cart-api" and r["level"] == "ERROR"
        )
        assert row["first_seen"] == "2026-01-01T10:20:00"

    def test_last_seen_is_maximum_timestamp_in_group(self, tmp_path, happy_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(happy_input), "--output", str(out))
        row = next(
            r for r in read_summary(out)
            if r["service"] == "cart-api" and r["level"] == "ERROR"
        )
        assert row["last_seen"] == "2026-01-01T10:25:00"

    def test_single_row_group_first_equals_last(self, tmp_path):
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "2026-03-15T09:00:00", "level": "WARN", "service": "svc", "message": "x"},
        ])
        out = tmp_path / "summary.csv"
        run_cli("--input", str(inp), "--output", str(out))
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["first_seen"] == rows[0]["last_seen"] == "2026-03-15T09:00:00"

    def test_first_last_seen_use_chronological_order_not_row_order(self, tmp_path):
        """first_seen is the chronologically earliest even when rows arrive out of order."""
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "2026-06-01T12:00:00", "level": "INFO", "service": "svc", "message": "later"},
            {"timestamp": "2026-06-01T08:00:00", "level": "INFO", "service": "svc", "message": "earlier"},
        ])
        out = tmp_path / "summary.csv"
        run_cli("--input", str(inp), "--output", str(out))
        rows = read_summary(out)
        assert rows[0]["first_seen"] == "2026-06-01T08:00:00"
        assert rows[0]["last_seen"]  == "2026-06-01T12:00:00"

    def test_output_has_required_columns_in_order(self, tmp_path, happy_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(happy_input), "--output", str(out))
        assert read_header(out) == ["service", "level", "count", "first_seen", "last_seen"]


# ── §2  Normalisation ─────────────────────────────────────────────────────────

class TestNormalisation:
    def test_level_lowercased_input_uppercased_in_output(self, tmp_path, padded_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(padded_input), "--output", str(out))
        levels = {r["level"] for r in read_summary(out)}
        assert levels == {"INFO", "ERROR"}
        assert "info" not in levels

    def test_level_whitespace_stripped(self, tmp_path, padded_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(padded_input), "--output", str(out))
        for r in read_summary(out):
            assert r["level"] == r["level"].strip()

    def test_service_whitespace_stripped(self, tmp_path, padded_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(padded_input), "--output", str(out))
        for r in read_summary(out):
            assert r["service"] == r["service"].strip()

    def test_service_original_casing_preserved(self, tmp_path):
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "2026-01-01T10:00:00", "level": "INFO", "service": "Cart-API", "message": "x"},
        ])
        out = tmp_path / "summary.csv"
        run_cli("--input", str(inp), "--output", str(out))
        assert read_summary(out)[0]["service"] == "Cart-API"

    def test_padded_service_merges_into_single_group(self, tmp_path, padded_input):
        """Two rows with the same service name but extra whitespace form one group."""
        out = tmp_path / "summary.csv"
        run_cli("--input", str(padded_input), "--output", str(out))
        services = {r["service"] for r in read_summary(out)}
        assert services == {"checkout-service"}


# ── §4  Missing level ─────────────────────────────────────────────────────────

class TestMissingLevel:
    def test_empty_level_normalised_to_unknown(self, tmp_path, missing_level_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(missing_level_input), "--output", str(out))
        levels = {r["level"] for r in read_summary(out)}
        assert "UNKNOWN" in levels

    def test_unknown_group_count_is_correct(self, tmp_path, missing_level_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(missing_level_input), "--output", str(out))
        unknown_rows = [r for r in read_summary(out) if r["level"] == "UNKNOWN"]
        assert len(unknown_rows) == 1  # one (cart-api, UNKNOWN) group
        assert int(unknown_rows[0]["count"]) == 2

    def test_warning_printed_to_stderr(self, tmp_path, missing_level_input):
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(missing_level_input), "--output", str(out))
        assert "WARNING" in stderr
        assert "missing level" in stderr.lower()

    def test_warning_states_affected_row_count(self, tmp_path, missing_level_input):
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(missing_level_input), "--output", str(out))
        assert "2" in stderr

    def test_quiet_suppresses_missing_level_warning(self, tmp_path, missing_level_input):
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(missing_level_input), "--output", str(out), "--quiet")
        assert stderr == ""

    def test_whitespace_only_level_normalised_to_unknown(self, tmp_path):
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "2026-01-01T10:00:00", "level": "   ", "service": "svc", "message": "x"},
        ])
        out = tmp_path / "summary.csv"
        run_cli("--input", str(inp), "--output", str(out))
        assert read_summary(out)[0]["level"] == "UNKNOWN"

    def test_absent_level_column_normalised_to_unknown(self, tmp_path):
        """CSV with no level column at all: every row is treated as absent level."""
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "2026-01-01T10:00:00", "service": "svc", "message": "x"},
        ], fieldnames=["timestamp", "service", "message"])
        out = tmp_path / "summary.csv"
        rc, _, stderr = run_cli("--input", str(inp), "--output", str(out))
        assert rc == 0
        assert read_summary(out)[0]["level"] == "UNKNOWN"
        assert "WARNING" in stderr


# ── §5  Malformed timestamp ───────────────────────────────────────────────────

class TestMalformedTimestamp:
    def test_bad_ts_rows_skipped(self, tmp_path, bad_ts_input):
        out = tmp_path / "summary.csv"
        rc, _, _ = run_cli("--input", str(bad_ts_input), "--output", str(out))
        assert rc == 0
        services = {r["service"] for r in read_summary(out)}
        assert "cart-api" not in services  # both cart-api rows had bad timestamps

    def test_valid_rows_still_appear_in_output(self, tmp_path, bad_ts_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(bad_ts_input), "--output", str(out))
        services = {r["service"] for r in read_summary(out)}
        assert "checkout-service" in services

    def test_warning_printed_to_stderr(self, tmp_path, bad_ts_input):
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(bad_ts_input), "--output", str(out))
        assert "WARNING" in stderr
        assert ("bad timestamp" in stderr.lower() or "skipped" in stderr.lower())

    def test_warning_states_skipped_row_count(self, tmp_path, bad_ts_input):
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(bad_ts_input), "--output", str(out))
        assert "2" in stderr

    def test_quiet_suppresses_bad_ts_warning(self, tmp_path, bad_ts_input):
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(bad_ts_input), "--output", str(out), "--quiet")
        assert stderr == ""

    def test_exit_code_0_despite_bad_timestamps(self, tmp_path, bad_ts_input):
        out = tmp_path / "summary.csv"
        rc, _, _ = run_cli("--input", str(bad_ts_input), "--output", str(out))
        assert rc == 0

    def test_skipped_rows_do_not_inflate_count(self, tmp_path):
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "2026-01-01T10:00:00", "level": "INFO", "service": "svc", "message": "good"},
            {"timestamp": "INVALID",              "level": "INFO", "service": "svc", "message": "bad"},
        ])
        out = tmp_path / "summary.csv"
        run_cli("--input", str(inp), "--output", str(out))
        assert int(read_summary(out)[0]["count"]) == 1

    def test_all_rows_bad_ts_yields_empty_output(self, tmp_path):
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "bad1", "level": "INFO",  "service": "svc", "message": "x"},
            {"timestamp": "bad2", "level": "ERROR", "service": "svc", "message": "y"},
        ])
        out = tmp_path / "summary.csv"
        rc, _, _ = run_cli("--input", str(inp), "--output", str(out))
        assert rc == 0
        assert read_summary(out) == []


# ── §6  Empty input ───────────────────────────────────────────────────────────

class TestEmptyInput:
    def test_header_only_csv_exits_0(self, tmp_path, empty_input):
        out = tmp_path / "summary.csv"
        rc, _, _ = run_cli("--input", str(empty_input), "--output", str(out))
        assert rc == 0

    def test_header_only_csv_produces_no_data_rows(self, tmp_path, empty_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(empty_input), "--output", str(out))
        assert read_summary(out) == []

    def test_output_header_is_correct_for_empty_input(self, tmp_path, empty_input):
        out = tmp_path / "summary.csv"
        run_cli("--input", str(empty_input), "--output", str(out))
        assert read_header(out) == ["service", "level", "count", "first_seen", "last_seen"]

    def test_notice_printed_to_stderr(self, tmp_path, empty_input):
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(empty_input), "--output", str(out))
        assert "NOTICE" in stderr
        assert "no data rows" in stderr.lower()

    def test_quiet_suppresses_empty_input_notice(self, tmp_path, empty_input):
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(empty_input), "--output", str(out), "--quiet")
        assert stderr == ""


# ── §7  CLI flags and exit codes ─────────────────────────────────────────────

class TestCLIFlags:
    def test_success_exits_0(self, tmp_path, happy_input):
        out = tmp_path / "summary.csv"
        rc, _, _ = run_cli("--input", str(happy_input), "--output", str(out))
        assert rc == 0

    def test_missing_input_file_exits_1(self, tmp_path):
        rc, _, _ = run_cli(
            "--input",  str(tmp_path / "nonexistent.csv"),
            "--output", str(tmp_path / "out.csv"),
        )
        assert rc == 1

    def test_custom_output_path_is_created(self, tmp_path, happy_input):
        custom = tmp_path / "my_output.csv"
        rc, _, _ = run_cli("--input", str(happy_input), "--output", str(custom))
        assert rc == 0
        assert custom.exists()

    def test_unknown_flag_exits_nonzero(self):
        rc, _, _ = run_cli("--not-a-real-flag")
        assert rc != 0

    def test_quiet_silences_all_stderr(self, tmp_path):
        """--quiet must suppress every notice and warning regardless of input issues."""
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "2026-01-01T10:00:00", "level": "INFO", "service": "svc", "message": "ok"},
            {"timestamp": "BAD",                  "level": "INFO", "service": "svc", "message": "bad ts"},
            {"timestamp": "2026-01-01T10:05:00",  "level": "",     "service": "svc", "message": "no level"},
        ])
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(inp), "--output", str(out), "--quiet")
        assert stderr == ""

    def test_both_warnings_emitted_when_both_issues_present(self, tmp_path):
        """Missing-level warning and bad-timestamp warning both appear."""
        inp = tmp_path / "events.csv"
        make_csv(inp, [
            {"timestamp": "2026-01-01T10:00:00", "level": "INFO", "service": "svc", "message": "good"},
            {"timestamp": "BAD",                  "level": "INFO", "service": "svc", "message": "bad ts"},
            {"timestamp": "2026-01-01T10:05:00",  "level": "",     "service": "svc", "message": "no level"},
        ])
        out = tmp_path / "summary.csv"
        _, _, stderr = run_cli("--input", str(inp), "--output", str(out))
        assert stderr.count("WARNING") >= 2
