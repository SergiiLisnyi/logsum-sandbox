import argparse
import csv
import sys
from datetime import datetime

OUTPUT_COLUMNS = ["service", "level", "count", "first_seen", "last_seen"]


def _parse_ts(value):
    try:
        return datetime.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def _warn(msg, quiet):
    if not quiet:
        print(msg, file=sys.stderr)


def _make_group(ts):
    return {"count": 0, "first_seen": ts, "last_seen": ts}


def summarise(input_path, output_path, quiet, min_count=1):
    try:
        fh = open(input_path, newline="", encoding="utf-8")  # noqa: SIM115
    except FileNotFoundError:
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    groups = {}
    total = missing_level = bad_ts = 0

    with fh:
        for row in csv.DictReader(fh):
            total += 1

            ts = _parse_ts(row.get("timestamp", ""))
            if ts is None:
                bad_ts += 1
                continue

            raw_level = row.get("level", "").strip().upper()
            level = raw_level or "UNKNOWN"
            if not raw_level:
                missing_level += 1

            service = row.get("service", "").strip()
            key = (service, level)
            g = groups.setdefault(key, _make_group(ts))
            g["count"] += 1
            g["first_seen"] = min(g["first_seen"], ts)
            g["last_seen"] = max(g["last_seen"], ts)

    if total == 0:
        _warn("NOTICE: input contained no data rows", quiet)
    if missing_level:
        _warn(f"WARNING: {missing_level} row(s) had missing level", quiet)
    if bad_ts:
        _warn(f"WARNING: {bad_ts} row(s) skipped (bad timestamp)", quiet)

    with open(output_path, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for (service, level), g in groups.items():
            if g["count"] < min_count:
                continue
            writer.writerow({
                "service": service,
                "level": level,
                "count": g["count"],
                "first_seen": g["first_seen"].isoformat(),
                "last_seen": g["last_seen"].isoformat(),
            })


def main():
    parser = argparse.ArgumentParser(description="Summarise event log CSV.")
    parser.add_argument("--input", default="data/events.csv", metavar="PATH")
    parser.add_argument("--output", default="data/summary.csv", metavar="PATH")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--min-count", type=int, default=1, metavar="N",
                        help="only output groups with count >= N (default: 1)")
    args = parser.parse_args()
    try:
        summarise(args.input, args.output, args.quiet, min_count=args.min_count)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
