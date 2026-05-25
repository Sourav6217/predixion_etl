# Predixion AI — ETL Pipeline

End-to-end data engineering pipeline that ingests raw, noisy voice-agent call logs,
cleans and transforms them, loads them into SQLite, and answers 5 business questions.

---
## 🌐 Live App

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://predixionai.streamlit.app/)

---

## Project Structure

```
predixion_etl/
├── generate.py        # Generates 500 raw call records with intentional noise
├── pipeline.py        # Ingestion → Validation → Transformation → Load (SQLite)
├── queries.py         # 5 business analytics queries → CSV outputs
├── requirements.txt   # Python dependencies
└── README.md
```

---

## Setup (fresh environment)

```bash
pip install -r requirements.txt
```

---

## How to Run (end-to-end)

**Step 1 — Generate raw data**
```bash
python generate.py
```
Creates `raw_calls.json` (500 records with ~15% missing fields, ~5% duplicates, ~3% bad timestamps)

**Step 2 — Run the pipeline**
```bash
python pipeline.py
```
OR with custom paths:
```bash
python pipeline.py --input raw_calls.json --db-path predixion.db
```
Outputs:
- `predixion.db` — SQLite database with `calls` and `ingestion_log` tables
- `rejected_log.csv` — All rejected records with rejection reason

**Step 3 — Run analytics queries**
```bash
python queries.py
```
Outputs 5 CSV files (one per business question):
- `q1_connect_rate.csv` — Connect rate by language
- `q2_callback_by_hour.csv` — Callback-requested rate by hour
- `q3_long_calls.csv` — Duration bucket distribution + avg amount
- `q4_top_agents.csv` — Top 3 agents with outcome breakdown
- `q5_volume_trend.csv` — Call volume by date

---

## Sample Output

```
--- INGESTION SUMMARY ---
Total records    : 500
Valid            : 403
Rejected         : 97
Rejection breakdown:
  missing_field    67
  duplicate        19
  bad_timestamp    11
```

---

## Design Choices

| Decision | Reason |
|---|---|
| Validate before dedup | Gives cleaner, more specific rejection reasons |
| Keep latest duplicate by start_time | Most recent record is most accurate |
| IST via `timedelta(hours=5, minutes=30)` | No external dependency (no pytz) |
| `amount_promised` nulls → 0 + flag | Preserves traceability of imputed values |
| `INSERT OR REPLACE` in SQLite | Makes pipeline fully idempotent — safe to re-run |
| CLI via argparse | Flexible for different environments and paths |

---

## What I Would Do Differently at Scale

- **Storage**: Replace SQLite with PostgreSQL or BigQuery; partition by `call_date`
- **Orchestration**: Schedule with Apache Airflow or Prefect with retry logic
- **Validation**: Add Great Expectations or Pydantic schema validation
- **Logging**: Structured JSON logging per stage with timings
- **Testing**: Unit tests for every transformation edge case
- **Streaming**: Replace batch JSON load with Kafka for real-time ingestion

---

## Tech Stack

Python 3.10+ | Pandas | SQLite (sqlite3) | No cloud or Spark required
