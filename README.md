# RestaurantOps

Offline starter for a fictional restaurant's operations dashboard. It creates
a local SQLite database, loads synthetic demo records, and prints a daily
snapshot of booked covers, staff shifts, units sold, sales in cents, and stock
currently below the target level. Python standard library only.

```sh
python3 restaurant_ops.py --db demo.sqlite3 seed-demo
python3 restaurant_ops.py --db demo.sqlite3 snapshot 2030-05-10
```

Use a scratch database for the demo. Re-running seed-demo preserves existing
records with the same IDs. Reservation and sales summaries are for the chosen
date. The stock alert reflects current stock. Demo timestamps are local.

The planned build adds a browser interface, reservation and shift changes,
inventory movements linked to recipe ingredients, sales import, and transparent
historical covers estimates. The starter is a read-only snapshot after seeding.
