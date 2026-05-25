import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
 
st.set_page_config(page_title="Predixion AI — Call Analytics", layout="wide", page_icon="📞")
 
# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: #0f1b2d;
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        text-align: center;
    }
    .metric-label { color: #7ea8c9; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { color: #e8f4fd; font-size: 2rem; font-weight: 700; margin-top: 4px; }
    .metric-sub   { color: #4a9eda; font-size: 0.82rem; margin-top: 2px; }
    h1, h2, h3 { color: #e8f4fd !important; }
    .stTabs [data-baseweb="tab"] { color: #7ea8c9; }
    .stTabs [aria-selected="true"] { color: #4a9eda !important; border-bottom: 2px solid #4a9eda; }
</style>
""", unsafe_allow_html=True)
 
# ── DB loader ─────────────────────────────────────────────────────────────────
@st.cache_data
def load(query):
    db = "predixion.db"
    if not os.path.exists(db):
        return None
    con = sqlite3.connect(db)
    df = pd.read_sql(query, con)
    con.close()
    return df
 
# ── Check DB ──────────────────────────────────────────────────────────────────
total_df = load("SELECT COUNT(*) as n FROM calls")
if total_df is None:
    st.error("❌ predixion.db not found. Run `python pipeline.py` first.")
    st.stop()
 
# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📞 Predixion AI — Call Analytics Dashboard")
st.caption("Voice agent call data · Ingested, cleaned & transformed via ETL pipeline")
st.divider()
 
# ── KPI Row ───────────────────────────────────────────────────────────────────
total     = load("SELECT COUNT(*) n FROM calls").iloc[0,0]
connected = load("SELECT COUNT(*) n FROM calls WHERE call_outcome='connected'").iloc[0,0]
long_pct  = load("SELECT ROUND(100.0*SUM(duration_bucket='long')/COUNT(*),1) p FROM calls").iloc[0,0]
avg_amt   = load("SELECT ROUND(AVG(amount_promised),0) a FROM calls WHERE is_amount_imputed=0").iloc[0,0]
rejected  = load("SELECT rejected_count FROM ingestion_log ORDER BY run_ts DESC LIMIT 1").iloc[0,0]
 
c1,c2,c3,c4,c5 = st.columns(5)
for col, label, val, sub in [
    (c1, "Total Calls", total, "clean records"),
    (c2, "Connect Rate", f"{round(connected/total*100,1)}%", f"{connected} connected"),
    (c3, "Long Calls", f"{long_pct}%", "> 300 seconds"),
    (c4, "Avg Amount Promised", f"₹{int(avg_amt):,}", "non-imputed only"),
    (c5, "Rejected Records", rejected, "in ingestion log"),
]:
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{val}</div>
        <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)
 
st.markdown("<br>", unsafe_allow_html=True)
 
# ── Tabs ──────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5 = st.tabs([
    "🌐 Connect Rate by Language",
    "⏰ Callback Rate by Hour",
    "⏱ Call Duration",
    "🏆 Top Agents",
    "📅 Volume Trend"
])
 
COLORS = ["#4a9eda","#2ecc9a","#f39c12","#e74c3c","#9b59b6"]
 
# Q1
with t1:
    df = load("""
        SELECT language,
               COUNT(*) total_calls,
               SUM(call_outcome='connected') connected,
               ROUND(100.0*SUM(call_outcome='connected')/COUNT(*),2) connect_rate_pct
        FROM calls GROUP BY language ORDER BY connect_rate_pct DESC
    """)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = px.bar(df, x="language", y="connect_rate_pct",
                     color="language", color_discrete_sequence=COLORS,
                     text="connect_rate_pct", title="Connect Rate (%) by Language")
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, yaxis_title="Connect Rate %",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#c9d8e8", yaxis=dict(gridcolor="#1e3a5f"))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Data Table")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"**Insight:** English has the highest connect rate at **{df.iloc[0]['connect_rate_pct']}%**.")
 
# Q2
with t2:
    df = load("""
        SELECT call_hour,
               COUNT(*) total,
               SUM(call_outcome='callback_requested') callbacks,
               ROUND(100.0*SUM(call_outcome='callback_requested')/COUNT(*),2) callback_rate_pct
        FROM calls GROUP BY call_hour ORDER BY call_hour
    """)
    top_hour = df.loc[df["callback_rate_pct"].idxmax(), "call_hour"]
    fig = px.line(df, x="call_hour", y="callback_rate_pct", markers=True,
                  title="Callback Requested Rate (%) by Hour of Day",
                  color_discrete_sequence=["#4a9eda"])
    fig.add_vline(x=top_hour, line_dash="dash", line_color="#f39c12",
                  annotation_text=f"Peak: {top_hour}:00", annotation_font_color="#f39c12")
    fig.update_layout(xaxis_title="Hour (24h)", yaxis_title="Callback Rate %",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#c9d8e8", yaxis=dict(gridcolor="#1e3a5f"),
                      xaxis=dict(tickmode="linear", dtick=1))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.sort_values("callback_rate_pct", ascending=False).head(5),
                 use_container_width=True, hide_index=True)
 
# Q3
with t3:
    df = load("""
        SELECT duration_bucket,
               COUNT(*) cnt,
               ROUND(100.0*COUNT()/SUM(COUNT(*)) OVER(),2) pct,
               ROUND(AVG(amount_promised),2) avg_amount
        FROM calls GROUP BY duration_bucket
    """)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(df, names="duration_bucket", values="cnt",
                     color_discrete_sequence=COLORS,
                     title="Call Duration Distribution", hole=0.45)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d8e8")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.bar(df, x="duration_bucket", y="avg_amount",
                      color="duration_bucket", color_discrete_sequence=COLORS,
                      text="avg_amount", title="Avg Amount Promised by Duration Bucket")
        fig2.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig2.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#c9d8e8",
                           yaxis=dict(gridcolor="#1e3a5f"))
        st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
 
# Q4
with t4:
    df = load("""
        SELECT agent_id, call_outcome, COUNT(*) cnt
        FROM calls
        WHERE agent_id IN (
            SELECT agent_id FROM calls GROUP BY agent_id ORDER BY COUNT(*) DESC LIMIT 3
        )
        GROUP BY agent_id, call_outcome ORDER BY agent_id, cnt DESC
    """)
    fig = px.bar(df, x="agent_id", y="cnt", color="call_outcome",
                 barmode="group", color_discrete_sequence=COLORS,
                 title="Top 3 Agents — Outcome Distribution",
                 text="cnt")
    fig.update_traces(textposition="outside")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#c9d8e8", yaxis=dict(gridcolor="#1e3a5f"),
                      xaxis_title="Agent", yaxis_title="Call Count")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
 
# Q5
with t5:
    df = load("""
        SELECT call_date, COUNT(*) total_calls
        FROM calls GROUP BY call_date ORDER BY call_date
    """)
    df["call_date"] = pd.to_datetime(df["call_date"])
    fig = px.area(df, x="call_date", y="total_calls",
                  title="Daily Call Volume Trend",
                  color_discrete_sequence=["#4a9eda"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#c9d8e8", yaxis=dict(gridcolor="#1e3a5f"),
                      xaxis_title="Date", yaxis_title="Calls")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.rename(columns={"call_date":"Date","total_calls":"Calls"}),
                 use_container_width=True, hide_index=True)
 
st.divider()
st.caption("Predixion AI · Data Engineering Internship Assignment · Sourav Manna")
