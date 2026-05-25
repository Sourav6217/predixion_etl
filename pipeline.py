import json, sqlite3, pandas as pd
from datetime import datetime, timezone, timedelta

REQUIRED_FIELDS = ["call_id","agent_id","customer_phone",
                   "start_time","end_time","call_outcome",
                   "language","disposition_code","retry_flag"]
IST = timezone(timedelta(hours=5, minutes=30))

def load_and_validate(path):
    with open(path) as f:
        raw = json.load(f)

    valid, rejected = [], []
    seen_ids = {}

    for rec in raw:
        # Missing fields
        missing = [f for f in REQUIRED_FIELDS if f not in rec]
        if missing:
            rejected.append({**rec, "reason": f"missing_field:{','.join(missing)}"})
            continue

        # Duplicate call_id — keep latest by start_time
        cid = rec["call_id"]
        if cid in seen_ids:
            existing = seen_ids[cid]
            try:
                if rec["start_time"] > existing["start_time"]:
                    rejected.append({**existing, "reason": "duplicate"})
                    seen_ids[cid] = rec
                else:
                    rejected.append({**rec, "reason": "duplicate"})
            except:
                rejected.append({**rec, "reason": "duplicate"})
            continue

        # Malformed timestamp
        try:
            datetime.fromisoformat(rec["start_time"])
            datetime.fromisoformat(rec["end_time"])
        except:
            rejected.append({**rec, "reason": "bad_timestamp"})
            continue

        seen_ids[cid] = rec

    valid = list(seen_ids.values())
    print(f"\n--- INGESTION SUMMARY ---")
    print(f"Total records    : {len(raw)}")
    print(f"Valid            : {len(valid)}")
    print(f"Rejected         : {len(rejected)}")
    
    rej_df = pd.DataFrame(rejected)
    if not rej_df.empty:
        print(rej_df["reason"].str.split(":").str[0].value_counts().to_string())

    return pd.DataFrame(valid), rej_df
