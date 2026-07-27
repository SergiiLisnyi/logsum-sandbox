# K 5.W.9 — By-hand vs by-agent comparison

## What both produced

Both the supervised chain (K 5.W.1–8) and a single-pass agent replay produce
the same visible deliverables:

- `src/logsum.py` — CLI that reads events CSV and writes a summary
- `tests/test_logsum.py` — pytest suite against the CLI
- `.github/workflows/ci.yml` — GitHub Actions lint + test gate
- `refactor-notes.md` — record of what the refactor removed
- `agent-task-note.md` — provenance note for the `--min-count` flag

The agent's pass runs in minutes; the supervised chain ran across K 5.W.1–8
with inspection at every step.

---

## Where the agent saved time

1. **Initial implementation (K 5.W.2).** The agent would have drafted all of
   `src/logsum.py` — argparse setup, CSV parsing, grouping loop, output
   writing — in one shot. In the supervised pass this took a full kata to write
   and another to test. Estimated saving: ~20–25 minutes of blank-page typing.

2. **Test scaffolding (K 5.W.4).** The agent would have generated the
   `TestGrouping`, `TestNormalisation`, `TestMissingLevel`,
   `TestMalformedTimestamp`, `TestEmptyInput`, and `TestCLIFlags` classes from
   `spec.md` in one prompt. The supervised pass produced 38 tests over a
   dedicated kata, but the structure would have emerged the same way either way.

3. **CI workflow (K 5.W.5).** A 19-line `ci.yml` is boilerplate the agent
   generates in seconds. It would have pinned nothing and produced the same
   unpinned `pip install ruff pytest` — identical to what the supervised pass
   produced.

---

## Where the agent went wrong or shorter

1. **ruff 0.16.0 breakage — no version pin.** The supervised pass hit this
   live: `pip install ruff` pulled 0.16.0, which enabled 413 default rules and
   broke CI on `BLE001`, `SIM115`, `PLW1510`, `PLR1730`, and `I001`. A single-
   pass agent would have produced the same unpinned workflow and the same
   breakage — but with no narrative. The supervised pass documented the failure,
   the root cause (default-rule expansion), and each noqa decision. An agent
   replay would have fixed the errors silently, leaving no record of *why* the
   noqa comments exist.

2. **Refactor silent-removal check missed.** During K 5.W.6, a candidate
   refactor replaced `if total == 0` with `if not groups`. The supervised review
   caught that this changes observable behaviour: if all rows have bad
   timestamps, `total > 0` but `groups` is empty — the refactor would wrongly
   emit the "no data rows" NOTICE. An unsupervised agent would likely have
   accepted the cleaner-looking substitution without testing this edge case
   (no test in the suite covers it).

3. **Incomplete provenance note.** The agent-task note for `--min-count` (K
   5.W.7) explicitly lists two untested items: `--min-count` above all group
   counts, and negative values. A single-pass agent writing its own provenance
   note tends to omit the "I did not test X" items — the note reads as complete
   when it is not.

---

## What the agent did better

1. **Speed on the `--min-count` flag (K 5.W.7).** The flag implementation —
   one param, one `continue`, one argparse line — is exactly the kind of
   bounded, well-specified change an agent handles without error. The supervised
   pass produced it in the same shape, but the agent would have done it in one
   shot with no back-and-forth. When the task is well-bounded and the spec is
   precise, agent speed is real.

2. **Consistent import ordering.** The agent would have generated
   `src/logsum.py` with sorted imports from the start (stdlib in alphabetical
   order, `from X import Y` after `import X`). The supervised pass needed a
   ruff 0.16.0 auto-fix to sort them later. A good agent uses ruff from the
   first draft.

---

## What I learned about supervised vs async

**Supervised work preserves the reasoning behind each decision.** The three
most valuable things in this chain are not the code — they are:
- Why the `total == 0` check was not replaced by `not groups`
- Why `# noqa: SIM115` and `# noqa: BLE001` exist and what they protect
- What the ruff 0.16.0 failure actually was, and how it was diagnosed

An async agent produces the same artefacts but none of the reasoning. The
next engineer who reads the code cannot tell whether the noqa comments are
lazy suppressions or deliberate guardrails.

**Async saves time on bounded, well-specified tasks.** The `--min-count` flag
is the canonical example: a single behaviour, one param, one filter line,
three tests. The agent would have produced this cleanly. The refactor review is
the canonical counter-example: the task requires reading what was removed and
comparing it against spec edge cases. An agent reviewing its own output will
not catch the `total == 0 → not groups` substitution.

---

## What I would do differently next time

1. **Pin `ruff==X.Y.Z` in `ci.yml` from the first commit.** An unpinned
   `pip install ruff` will break CI every time a major version ships with
   expanded default rules. The correct fix is a `pyproject.toml` with
   `[tool.ruff]` and a pinned dev dependency, not after-the-fact noqa comments.

2. **Add a test for "all rows have bad timestamps → no NOTICE."** The spec
   edge case exists; the test does not. If the test existed, the
   `total == 0 → not groups` refactor would have been caught automatically
   instead of requiring a manual read of the diff.

3. **Write the provenance note before pushing, not after.** The note template
   has an "untested items" section for a reason — writing it before the push
   forces a deliberate check of what was not verified, not a retrospective
   guess.
