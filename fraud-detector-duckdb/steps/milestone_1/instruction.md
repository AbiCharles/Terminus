Our fraud team keeps all of its transaction data inside a DuckDB database and I want a small detection pipeline built directly on top of it — no CSV exports, everything stays in the database. It's all under /app.

The database is at `/app/fraud.duckdb` and the data contracts are written up in `/app/spec.md` — read that first. It describes the raw `transactions` table you start from and every table and artifact you need to produce. Over three milestones you'll build a behavioural feature table with SQL window functions, train a scikit-learn classifier and save it alongside its evaluation metrics, then write a small CLI that batch-scores transactions back into the database.

Milestone 1: build the `features` table from section 2 of the spec — one row per transaction, with the per-account behavioural window features computed over each account's transaction history. Use DuckDB's window functions against the `transactions` table, and leave `transactions` itself unchanged.
