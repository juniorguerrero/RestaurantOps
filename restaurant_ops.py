"""Load synthetic restaurant records and print a daily operations snapshot."""

import argparse
from datetime import date
import json
from pathlib import Path
import sqlite3

DEMO_PATH = Path(__file__).parent / "examples" / "demo.json"
SCHEMA = """
CREATE TABLE IF NOT EXISTS inventory (
    item TEXT PRIMARY KEY, unit TEXT NOT NULL,
    on_hand INTEGER NOT NULL CHECK (on_hand >= 0),
    par INTEGER NOT NULL CHECK (par >= 0)
);
CREATE TABLE IF NOT EXISTS reservations (
    id TEXT PRIMARY KEY, starts_at TEXT NOT NULL,
    party_size INTEGER NOT NULL CHECK (party_size > 0)
);
CREATE TABLE IF NOT EXISTS shifts (
    id TEXT PRIMARY KEY, staff TEXT NOT NULL, role TEXT NOT NULL,
    starts_at TEXT NOT NULL, ends_at TEXT NOT NULL CHECK (ends_at > starts_at)
);
CREATE TABLE IF NOT EXISTS sales (
    id TEXT PRIMARY KEY, sold_at TEXT NOT NULL, item TEXT NOT NULL,
    units INTEGER NOT NULL CHECK (units > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0)
);
"""
SEED_STATEMENTS = {
    "inventory": "INSERT INTO inventory VALUES (:item, :unit, :on_hand, :par) ON CONFLICT DO NOTHING",
    "reservations": "INSERT INTO reservations VALUES (:id, :starts_at, :party_size) ON CONFLICT DO NOTHING",
    "shifts": "INSERT INTO shifts VALUES (:id, :staff, :role, :starts_at, :ends_at) ON CONFLICT DO NOTHING",
    "sales": "INSERT INTO sales VALUES (:id, :sold_at, :item, :units, :unit_price_cents) ON CONFLICT DO NOTHING",
}


def seed_demo(db):
    fixture = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
    with db:
        for table, statement in SEED_STATEMENTS.items():
            db.executemany(statement, fixture[table])


def snapshot(db, day):
    day_key = day.isoformat()
    reservations, covers = db.execute(
        "SELECT COUNT(*), COALESCE(SUM(party_size), 0) "
        "FROM reservations WHERE substr(starts_at, 1, 10) = ?", (day_key,)
    ).fetchone()
    units, revenue = db.execute(
        "SELECT COALESCE(SUM(units), 0), COALESCE(SUM(units * unit_price_cents), 0) "
        "FROM sales WHERE substr(sold_at, 1, 10) = ?", (day_key,)
    ).fetchone()
    shifts = db.execute(
        "SELECT staff, role, starts_at, ends_at FROM shifts "
        "WHERE substr(starts_at, 1, 10) <= ? AND ends_at > ? ORDER BY starts_at, id",
        (day_key, f"{day_key}T00:00")
    )
    stock = db.execute(
        "SELECT item, unit, on_hand, par FROM inventory WHERE on_hand < par ORDER BY item"
    )
    return {
        "date": day_key, "reservations": reservations, "booked_covers": covers,
        "units_sold": units, "sales_cents": revenue,
        "shifts": [dict(row) for row in shifts],
        "current_stock_below_par": [dict(row) for row in stock],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("seed-demo")
    daily = sub.add_parser("snapshot")
    daily.add_argument("date", type=date.fromisoformat)
    args = parser.parse_args()
    try:
        with sqlite3.connect(args.db) as db:
            db.row_factory = sqlite3.Row
            db.executescript(SCHEMA)
            if args.action == "seed-demo":
                seed_demo(db)
                print("Synthetic restaurant data loaded.")
            else:
                print(json.dumps(snapshot(db, args.date), indent=2))
    except (OSError, sqlite3.Error) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
