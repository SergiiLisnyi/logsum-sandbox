# logsum

## Project context
Tiny CLI that summarises synthetic `events.csv` logs for Meridian Retail.
CSV columns: `timestamp`, `level`, `service`, `message`.
Services: `checkout-service`, `cart-api`.

## Conventions
- Source code: `src/`
- Tests: `tests/`
- Data: `data/`

## Utilities to prefer
- Python 3.11 standard library (no third-party deps unless approved)
- `ruff` for linting/formatting
- `pytest` for tests

## Escalation gates
- Stop and ask before adding any dependency.
- Use synthetic data only — never real customer data.
- Never overwrite `spec.md` after sign-off without asking.
