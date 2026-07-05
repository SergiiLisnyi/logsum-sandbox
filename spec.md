# logsum — CLI Specification

## Goal
Read a CSV log file and write a grouped summary CSV.
One output row per `(service, level)` pair, with event count and time bounds.

## Inputs
File: `events.csv` (default path `data/events.csv`).

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | ISO-8601 string | When the event occurred |
| `level` | string | Severity label (e.g. `INFO`, `ERROR`) |
| `service` | string | Originating service name |
| `message` | string | Human-readable event description (not used in grouping) |

## 1. Group key
Rows are grouped by the composite key `(service, level)`.
Output contains one row per unique pair.

## 2. Normalisation rules
- `level`: strip surrounding whitespace, uppercase (e.g. `info` → `INFO`).
- `service`: strip surrounding whitespace; preserve original casing.
- No other transforms are applied to input values.

## 3. Output columns
`service, level, count, first_seen, last_seen`
`first_seen` and `last_seen` are ISO-8601 strings derived from the earliest
and latest valid `timestamp` values in the group.

## 4. Missing level behaviour
- An empty or absent `level` value is normalised to `UNKNOWN`.
- The row is included in output under the `UNKNOWN` level.
- A warning is emitted to stderr: `WARNING: N row(s) had missing level`.

## 5. Malformed timestamp behaviour
- Rows with an unparseable `timestamp` are skipped entirely.
- They do not contribute to any group's `count`, `first_seen`, or `last_seen`.
- After processing, stderr reports: `WARNING: N row(s) skipped (bad timestamp)`.
- Processing continues; the CLI does not abort.

## 6. Empty input behaviour
- A CSV with only a header row (or zero rows) is valid input.
- Output is a header-only `summary.csv`.
- Stderr prints: `NOTICE: input contained no data rows`.
- Exit code: 0.

## 7. CLI flags and exit codes

| Flag | Default | Description |
|------|---------|-------------|
| `--input PATH` | `data/events.csv` | Path to input CSV |
| `--output PATH` | `data/summary.csv` | Path to output CSV |
| `--quiet` | off | Suppress all stderr notices and warnings |

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Bad arguments or input file not found |
| 2 | Unhandled internal error |

## 8. Out of scope
- Filtering by date range, service, or level
- Streaming / watch mode
- Database, JSON, or Parquet output
- Real customer data (synthetic data only)
- Internationalisation

## Implementation notes
`datetime.fromisoformat()` was chosen over manual `strptime` patterns because Python 3.11 extended it to cover the full ISO-8601 subset the spec requires, keeping timestamp parsing to a single stdlib call with no format list to maintain.

## Signed off
Sergii_Lisnyi — 2026-07-05
