import json
import sqlite3
import pandas as pd
from datetime import datetime, timezone, timedelta
import argparse
 
REQUIRED_FIELDS = ["call_id", "agent_id", "customer_phone",
                   "start_time", "end_time", "call_outcome",
                   "language", "disposition_code", "retry_flag"]
IST = timezone(timedelta(hours=5, minutes=30))
 
 
def load_and_validate(path):
    with open(path) as f:
        raw = json.load(f)
 
    rejected = []
    seen_ids = {}
 
    for rec in raw:
        # Missing fields check
        missing = [f for f in REQUIRED_FIELDS if f not in rec]
        if missing:
            rejected.append({**rec, "reason": f"missing_field:{','.join(missing)}"})
            continue
 
        # Malformed timestamp check
        try:
            datetime.fromisoformat(rec["start_time"])
            datetime.fromisoformat(rec["end_time"])
        except Exception:
            rejected.append({**rec, "reason": "bad_timestamp"})
            continue
 
        # Duplicate call_id — keep latest by start_time
        cid = rec["call_id"]
        if cid in seen_ids:
            existing = seen_ids[cid]
            if rec["start_time"] > existing["start_time"]:
                rejected.append({**existing, "reason": "duplicate"})
                seen_ids[cid] = rec
            else:
                rejected.append({**rec, "reason": "duplicate"})
        else:
            seen_ids[cid] = rec
 
    valid = list(seen_ids.values())
 
    print("\n--- INGESTION SUMMARY ---")
    print(f"Total records    : {len(raw)}")
    print(f"Valid            : {len(valid)}")
    print(f"Rejected         : {len(rejected)}")
 
    rej_df = pd.DataFrame(rejected)
    if not rej_df.empty:
        breakdown = rej_df["reason"].str.split(":").str[0].value_counts()
        print("Rejection breakdown:")
        print(breakdown.to_string())
 
    return pd.DataFrame(valid), rej_df
 
 
def transform(df):
    # Parse timestamps to IST
    df["start_time"] = pd.to_datetime(df["start_time"], utc=True).dt.tz_convert(IST)
    df["end_time"]   = pd.to_datetime(df["end_time"],   utc=True).dt.tz_convert(IST)
 
    df["call_duration_seconds"] = (
        (df["end_time"] - df["start_time"]).dt.total_seconds().astype(int)
    )
    df["call_hour"]  = df["start_time"].dt.hour
    df["call_date"]  = df["start_time"].dt.date.astype(str)
    df["is_weekend"] = df["start_time"].dt.dayofweek >= 5
 
    def bucket(s):
        if s < 60:
            return "short"
        elif s <= 300:
            return "medium"
        else:
            return "long"
 
    df["duration_bucket"] = df["call_duration_seconds"].apply(bucket)
 
    # Impute amount_promised
    df["is_amount_imputed"] = df["amount_promised"].isna()
    df["amount_promised"]   = df["amount_promised"].fillna(0)
 
    # Convert booleans to int for SQLite
    df["is_weekend"]        = df["is_weekend"].astype(int)
    df["is_amount_imputed"] = df["is_amount_imputed"].astype(int)
    df["retry_flag"]        = df["retry_flag"].astype(int)
 
    # Strip timezone for SQLite
    df["start_time"] = df["start_time"].astype(str)
    df["end_time"]   = df["end_time"].astype(str)
 
    return df
 
 
def load_to_sqlite(df, rej_df, db_path="predixion.db"):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            call_id TEXT PRIMARY KEY,
            agent_id TEXT,
            customer_phone TEXT,
            start_time TEXT,
            end_time TEXT,
            call_outcome TEXT,
            language TEXT,
            disposition_code TEXT,
            amount_promised REAL,
            retry_flag INTEGER,
            call_duration_seconds INTEGER,
            call_hour INTEGER,
            call_date TEXT,
            is_weekend INTEGER,
            duration_bucket TEXT,
            is_amount_imputed INTEGER
        )
    """)
 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_log (
            run_ts TEXT,
            records_processed INTEGER,
            rejected_count INTEGER
        )
    """)
 
    # Idempotent upsert
    for _, row in df.iterrows():
        cur.execute("""
            INSERT OR REPLACE INTO calls VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, tuple(row[c] for c in [
            "call_id", "agent_id", "customer_phone", "start_time", "end_time",
            "call_outcome", "language", "disposition_code", "amount_promised",
            "retry_flag", "call_duration_seconds", "call_hour", "call_date",
            "is_weekend", "duration_bucket", "is_amount_imputed"
        ]))
 
    cur.execute(
        "INSERT INTO ingestion_log VALUES (?,?,?)",
        (datetime.now().isoformat(), len(df), len(rej_df))
    )
 
    con.commit()
    con.close()
    print(f"\nLoaded {len(df)} clean records into {db_path}")
 
 
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Predixion AI ETL Pipeline")
    ap.add_argument("--input",   default="raw_calls.json", help="Path to raw JSON file")
    ap.add_argument("--db-path", default="predixion.db",   help="Path to SQLite DB")
    args = ap.parse_args()
 
    raw_df, rej_df = load_and_validate(args.input)
    clean_df = transform(raw_df)
    load_to_sqlite(clean_df, rej_df, args.db_path)
    rej_df.to_csv("rejected_log.csv", index=False)
    print("Done. rejected_log.csv written.")
