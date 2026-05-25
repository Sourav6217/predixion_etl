## Predixion AI — ETL Pipeline

### Setup
pip install -r requirements.txt

### Run end-to-end
python generate.py          # creates raw_calls.json
python pipeline.py          # ingests, transforms, loads → predixion.db
python queries.py           # generates 5 CSV answers

### CLI flags
python pipeline.py --input raw_calls.json --db-path predixion.db

### Design Choices
- Validation before dedup → cleaner rejection reasons
- IST normalization via pytz-free timedelta
- INSERT OR REPLACE makes pipeline idempotent
- amount_promised nulls → 0 + is_amount_imputed flag

### At Scale
- Replace SQLite with PostgreSQL / BigQuery
- Use Airflow or Prefect for scheduling
- Add Great Expectations for schema validation
- Partition by call_date for query performance
