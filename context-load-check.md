# CLAUDE.md summary

From [CLAUDE.md](CLAUDE.md):

**Project context** — A tiny CLI that summarises synthetic `events.csv` logs (columns: `timestamp`, `level`, `service`, `message`) for Meridian Retail's `checkout-service` and `cart-api`.

**Conventions** — Code in `src/`, tests in `tests/`, data in `data/`.

**Utilities to prefer** — Python 3.11 stdlib, `ruff` for linting/formatting, `pytest` for tests.

**Escalation gates** — Three hard stops: ask before adding dependencies, use synthetic data only, never overwrite `spec.md` post-sign-off without asking.
