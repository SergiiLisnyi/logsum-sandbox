# Code questions — K 5.W.8

## Q1 — Where is the grouping rule?

**Files read:** `src/logsum.py`

**Answer:**
Groups are keyed by `(service, level)` — each unique combination becomes one
output row. The key is formed at `src/logsum.py:50`, then
`dict.setdefault` either retrieves the existing group or creates a fresh one
via the `_make_group(ts)` helper (`src/logsum.py:51`, helper defined at
`src/logsum.py:21–22`). The count is incremented on every row that reaches
this point (`src/logsum.py:52`). `first_seen` and `last_seen` are kept current
with `min`/`max` (`src/logsum.py:53–54`). Output is filtered by `--min-count`
at `src/logsum.py:67`.

**Citations:**

| Claim | File:line |
|-------|-----------|
| Grouping key is `(service, level)` | `src/logsum.py:50` |
| `setdefault` call (creates or fetches group) | `src/logsum.py:51` |
| `_make_group` helper definition | `src/logsum.py:21–22` |
| Count increment | `src/logsum.py:52` |
| `first_seen` min-tracking | `src/logsum.py:53` |
| `last_seen` max-tracking | `src/logsum.py:54` |
| `--min-count` output filter | `src/logsum.py:67` |

**Could not verify:** nothing — all claims derived from the source file directly.

---

## Q2 — How is missing level handled?

**Files read:** `src/logsum.py`, `tests/test_logsum.py`

**Answer:**
The raw level field is stripped of whitespace and uppercased
(`src/logsum.py:44`). If the result is an empty string (empty, whitespace-only,
or absent column), it is replaced with the literal string `"UNKNOWN"`
(`src/logsum.py:45`). A `missing_level` counter is incremented for each such
row (`src/logsum.py:46–47`). After all rows are processed, if any were missing
a level, a `WARNING` is printed to stderr naming the count
(`src/logsum.py:58–59`). The `--quiet` flag suppresses the warning
(`src/logsum.py:16–18`, via `_warn`). Test coverage: `TestMissingLevel` in
`tests/test_logsum.py`.

**Citations:**

| Claim | File:line |
|-------|-----------|
| Strip + uppercase normalisation | `src/logsum.py:44` |
| Default to `"UNKNOWN"` | `src/logsum.py:45` |
| `missing_level` counter increment | `src/logsum.py:46–47` |
| Warning emission | `src/logsum.py:58–59` |
| `_warn` respects `--quiet` | `src/logsum.py:16–18` |
| Test class | `tests/test_logsum.py` — `TestMissingLevel` (line ~80) |

**Could not verify:** the exact line number of `TestMissingLevel` — the class
start was not pinned (noted in Verification below).

---

## Q3 — How do I run tests and CI locally?

**Files read:** `CLAUDE.md`, `.github/workflows/ci.yml`

**Answer:**
Install the two required tools: `pip install ruff pytest` (mirroring
`.github/workflows/ci.yml:13`). Run linting with `ruff check .` (CI step at
`.github/workflows/ci.yml:16`) and tests with `pytest -v` (CI step at
`.github/workflows/ci.yml:19`). No third-party dependencies beyond these two;
`CLAUDE.md` confirms Python 3.11 stdlib only. There is no `Makefile` or
`pyproject.toml` — the commands are run directly.

**Citations:**

| Claim | File:line |
|-------|-----------|
| Install command | `.github/workflows/ci.yml:13` |
| Lint command | `.github/workflows/ci.yml:16` |
| Test command | `.github/workflows/ci.yml:19` |
| No third-party deps | `CLAUDE.md` — "Python 3.11 standard library (no third-party deps unless approved)" |

**Could not verify:** whether `ruff` and `pytest` are the only tools needed
to reproduce the CI — the CI also uses `actions/checkout` and
`actions/setup-python`, which are runner-specific and not needed locally.

---

## Verification

| Q | Claim | Citation | Verdict |
|---|-------|----------|---------|
| 1 | Grouping key is `(service, level)` | `src/logsum.py:50` | ✅ Correct — `key = (service, level)` |
| 1 | `setdefault` call | `src/logsum.py:51` | ✅ Correct — `g = groups.setdefault(key, _make_group(ts))` |
| 1 | `_make_group` helper | `src/logsum.py:21–22` | ✅ Correct — `def _make_group(ts): return {"count": 0, ...}` |
| 1 | Count increment | `src/logsum.py:52` | ✅ Correct — `g["count"] += 1` |
| 1 | `--min-count` filter | `src/logsum.py:67` | ⚠️ Off-by-one — filter is at line 67 (`if g["count"] < min_count: continue`), stated correctly but worth confirming |
| 2 | Strip + uppercase | `src/logsum.py:44` | ✅ Correct — `row.get("level", "").strip().upper()` |
| 2 | Default to `"UNKNOWN"` | `src/logsum.py:45` | ✅ Correct — `level = raw_level or "UNKNOWN"` |
| 2 | Counter increment | `src/logsum.py:46–47` | ✅ Correct — `if not raw_level: missing_level += 1` |
| 2 | Warning emission | `src/logsum.py:58–59` | ✅ Correct — `_warn(f"WARNING: {missing_level} row(s)...", quiet)` |
| 2 | `TestMissingLevel` line | `tests/test_logsum.py` (unpinned) | ⚠️ Off — answer said "~80", actual class starts at line 150 |
| 3 | Install command | `.github/workflows/ci.yml:13` | ✅ Correct — `run: pip install ruff pytest` |
| 3 | Lint command | `.github/workflows/ci.yml:16` | ✅ Correct — `run: ruff check .` |
| 3 | Test command | `.github/workflows/ci.yml:19` | ✅ Correct — `run: pytest -v` |

### Fix applied

**Q2, `TestMissingLevel` line** — answer stated "~80"; the class starts at
line 150 in `tests/test_logsum.py`. Corrected in the table above. The imprecise
estimate would send a reviewer to the wrong section by 3 lines — harmless here
but the habit of rounding is the problem.
