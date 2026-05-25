import json, random, uuid
from datetime import datetime, timedelta

random.seed(42)

AGENTS = [f"AGT{i:03d}" for i in range(1, 11)]
OUTCOMES = ["connected", "no_answer", "dropped", "callback_requested"]
LANGUAGES = ["Hindi", "English", "Marathi"]
DISPOSITIONS = ["D01", "D02", "D03", "D04", "D05"]

def random_time():
    base = datetime(2024, 6, 1)
    return base + timedelta(days=random.randint(0, 29),
                            hours=random.randint(8, 20),
                            minutes=random.randint(0, 59))

records = []
for i in range(475):  # 500 after duplicates
    start = random_time()
    end = start + timedelta(seconds=random.randint(10, 600))
    record = {
        "call_id": str(uuid.uuid4()),
        "agent_id": random.choice(AGENTS),
        "customer_phone": f"9{random.randint(100000000, 999999999)}",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "call_outcome": random.choice(OUTCOMES),
        "language": random.choice(LANGUAGES),
        "disposition_code": random.choice(DISPOSITIONS),
        "amount_promised": round(random.uniform(500, 50000), 2) if random.random() > 0.3 else None,
        "retry_flag": random.choice([True, False])
    }

    # ~15% missing fields
    if random.random() < 0.15:
        field = random.choice(["agent_id", "call_outcome", "language", "end_time"])
        del record[field]

    # ~3% malformed timestamps
    if random.random() < 0.03:
        record["start_time"] = "NOT-A-DATE"

    records.append(record)

# ~5% duplicates
dupes = random.sample(records, 25)
records.extend(dupes)
random.shuffle(records)

with open("raw_calls.json", "w") as f:
    json.dump(records, f, indent=2)

print(f"Generated {len(records)} records → raw_calls.json")
