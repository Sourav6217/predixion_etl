import sqlite3, pandas as pd

con = sqlite3.connect("predixion.db")

# Q1 — Connect rate by language
q1 = pd.read_sql("""
    SELECT language,
           COUNT(*) total_calls,
           SUM(call_outcome='connected') connected,
           ROUND(100.0*SUM(call_outcome='connected')/COUNT(*),2) connect_rate_pct
    FROM calls GROUP BY language
""", con)
print("\nQ1 — Connect rate by language:\n", q1)
q1.to_csv("q1_connect_rate.csv", index=False)

# Q2 — Hour with highest callback_requested rate
q2 = pd.read_sql("""
    SELECT call_hour,
           COUNT(*) total,
           SUM(call_outcome='callback_requested') callbacks,
           ROUND(100.0*SUM(call_outcome='callback_requested')/COUNT(*),2) callback_rate_pct
    FROM calls GROUP BY call_hour ORDER BY callback_rate_pct DESC LIMIT 5
""", con)
print("\nQ2 — Top hours by callback rate:\n", q2)
q2.to_csv("q2_callback_by_hour.csv", index=False)

# Q3 — Long calls %  and avg amount_promised
q3 = pd.read_sql("""
    SELECT duration_bucket,
           COUNT(*) cnt,
           ROUND(100.0*COUNT()/SUM(COUNT(*)) OVER(),2) pct,
           ROUND(AVG(amount_promised),2) avg_amount
    FROM calls GROUP BY duration_bucket
""", con)
print("\nQ3 — Duration distribution:\n", q3)
q3.to_csv("q3_long_calls.csv", index=False)

# Q4 — Top 3 agents with outcome distribution
q4 = pd.read_sql("""
    SELECT agent_id, call_outcome, COUNT(*) cnt
    FROM calls
    WHERE agent_id IN (
        SELECT agent_id FROM calls GROUP BY agent_id ORDER BY COUNT(*) DESC LIMIT 3
    )
    GROUP BY agent_id, call_outcome ORDER BY agent_id, cnt DESC
""", con)
print("\nQ4 — Top 3 agents outcome distribution:\n", q4)
q4.to_csv("q4_top_agents.csv", index=False)

# Q5 — Call volume by date
q5 = pd.read_sql("""
    SELECT call_date, COUNT(*) total_calls
    FROM calls GROUP BY call_date ORDER BY call_date
""", con)
print("\nQ5 — Call volume trend:\n", q5)
q5.to_csv("q5_volume_trend.csv", index=False)

con.close()
print("\nAll query CSVs written.")
