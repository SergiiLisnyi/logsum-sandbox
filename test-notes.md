# Test notes

## 1. Isolation method

Tests never read, import, or examine `src/logsum.py`.
Every test invokes the CLI as an opaque subprocess via `subprocess.run` and asserts only on observable outputs: the exit code, stderr text, and the content of the output CSV.

Three concrete boundaries enforce this:

- **Process boundary** — `src/logsum.py` runs in a child process; the test has no access to its internal objects or state.
- **Filesystem boundary** — input CSVs are constructed programmatically with `make_csv()` into pytest's `tmp_path`; the output CSV is read back with `csv.DictReader`. No test touches `data/` or any file that belongs to the implementation.
- **Interface boundary** — assertions target the public contract (column names, field values, exit codes, stderr keywords). Internal variable names, class structure, and algorithm choices are invisible to every test.

The result: any correct reimplementation of the spec will pass the suite without touching a single test; any deviation from the spec will break at least one assertion.

## 2. Test that would catch a real bug

```python
def test_first_last_seen_use_chronological_order_not_row_order(self, tmp_path):
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
```

**Bug it catches:** an implementation that accumulates timestamps by row order — recording the first row seen as `first_seen` and the last row as `last_seen` — instead of tracking the chronological minimum and maximum.

With that bug the fixture above produces:

```
first_seen = "2026-06-01T12:00:00"   # wrong: first row, not earliest time
last_seen  = "2026-06-01T08:00:00"   # wrong: last row, not latest time
```

The spec requires `first_seen` and `last_seen` to be derived from the *earliest* and *latest* valid timestamps in the group, so both assertions fail, pinpointing exactly where the implementation went wrong.
