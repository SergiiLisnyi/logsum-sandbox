# Agent task provenance — K 5.W.7

## Task
Add `--min-count N` to `src/logsum.py`. When set, output only groups whose
count is >= N. Default behaviour stays unchanged. Update `spec.md` and
`tests/test_logsum.py`.

## Agent
Model: Claude Sonnet 4.6 (claude-sonnet-4-6)

## Context loaded
- `src/logsum.py` — full file read before editing
- `tests/test_logsum.py` — tail inspected to find insertion point
- `spec.md` — tail inspected to find insertion point
- K 5.W.7 kata spec (`500-wide-katas.md`) — task boundary confirmed

## Files changed
| File | Change |
|------|--------|
| `src/logsum.py` | Added `min_count=1` param to `summarise()`; added `if g["count"] < min_count: continue` in output loop; added `--min-count` argparse argument |
| `tests/test_logsum.py` | Added `TestMinCount` class with 3 tests |
| `spec.md` | Added §8 — --min-count flag |
| `agent-task-note.md` | This file |

## Plan deviations
None. The task was executed exactly as planned: one flag, filter in the
output loop, no changes to parsing/normalisation/warning paths.

## Untested items
- `--min-count` with a value larger than all group counts (output is an empty
  CSV with a header). The spec says output-only filtering; the header is still
  written. Not explicitly tested — the existing `test_header_only_csv_*` tests
  cover the empty-output case for other inputs.
- Negative values for `--min-count` (e.g. `--min-count -1`). argparse accepts
  negative integers; `-1 <= any count` so all groups are kept. Behaviour is
  correct but not explicitly tested.
