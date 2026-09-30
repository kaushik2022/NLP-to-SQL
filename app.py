"""
app.py
Streamlit Web Application for the NLP to SQL Query Assistant.
Features LangGraph orchestration, live SQLite schema inspection, SQL security validation,
interactive tabular data display, data visualization, and conversational synthesis.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import streamlit as st

# Configure sys.path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import SQLiteDatabase
from src.sql_agent import NLToSQLAgent
from src.config import settings
from seed_database import init_db

# Streamlit Page Config
st.set_page_config(
    page_title="NLP to SQL Query Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-badge {
        display: inline-block;
        padding: 4px 12px;
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 9999px;
        color: #1D4ED8;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .status-ok {
        color: #16A34A;
        font-weight: 600;
    }
    .sql-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "current_query" not in st.session_state:
    st.session_state.current_query = "Who are the top 5 highest paid employees?"

# Ensure SQLite database exists
if not settings.db_path.exists():
    init_db(settings.db_path)

db = SQLiteDatabase(settings.db_path)
agent = NLToSQLAgent(db=db)

# ================= SIDEBAR =================
with st.sidebar:
    st.title("⚙️ System & Controls")
    
    # Model Configuration
    st.subheader("Model Configuration")
    gemini_key = st.text_input(
        "Gemini API Key (Optional)",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Provide a Gemini API key for dynamic generation, or leave blank to use the built-in local schema generator."
    )
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        settings.gemini_api_key = gemini_key
        st.success("API Key Active (Live LLM Mode)")
    else:
        st.info("Local Zero-API Engine Active")

    st.markdown("---")

    # Live Database Inspector
    st.subheader("📊 SQLite Database Inspector")
    st.caption(f"Connected DB: `{settings.db_path.name}`")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cursor.fetchall()]
    
    selected_table = st.selectbox("Explore Table Schema & Data", tables)
    if selected_table:
        cursor.execute(f"SELECT COUNT(*) FROM '{selected_table}';")
        count = cursor.fetchone()[0]
        st.markdown(f"**Total Records:** `{count}`")
        
        # Schema columns
        cursor.execute(f"PRAGMA table_info('{selected_table}');")
        cols = cursor.fetchall()
        schema_df = pd.DataFrame([{"Column": c[1], "Type": c[2], "PK": bool(c[5])} for c in cols])
        st.dataframe(schema_df, use_container_width=True, hide_index=True)
        
        # Sample Preview
        cursor.execute(f"SELECT * FROM '{selected_table}' LIMIT 3;")
        sample_rows = [dict(r) for r in cursor.fetchall()]
        if sample_rows:
            with st.expander(f"Preview {selected_table} (3 rows)"):
                st.dataframe(pd.DataFrame(sample_rows), use_container_width=True, hide_index=True)
    conn.close()

    st.markdown("---")
    
    # Reset Database Option
    if st.button("🔄 Reset / Re-seed SQLite DB"):
        init_db(settings.db_path)
        st.success("Database reset to initial sample records!")
        st.rerun()

# ================= MAIN CONTENT =================
st.markdown('<div class="main-title">🔍 NLP to SQL Query Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Translate natural language questions into safe, optimized SQL executed with sub-millisecond latency on local SQLite via LangGraph.</div>',
    unsafe_allow_html=True
)

# Sample Query Chips
st.markdown("**Sample Business Questions (Click to populate):**")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🏆 Top 5 highest paid employees"):
        st.session_state.current_query = "Who are the top 5 highest paid employees?"
    if st.button("💰 Total sales revenue and deals"):
        st.session_state.current_query = "What is the total sales revenue and number of deals won?"
with col2:
    if st.button("🏢 Average salary by department"):
        st.session_state.current_query = "What is the average salary across each department?"
    if st.button("🚀 Projects currently in progress"):
        st.session_state.current_query = "List all company projects and their budgets."
with col3:
    if st.button("👤 Sales revenue by representative"):
        st.session_state.current_query = "Which sales representative generated the most revenue?"
    if st.button("👥 Employee headcount per department"):
        st.session_state.current_query = "How many employees are in each department?"

# User Query Input Form
with st.form("query_form", clear_on_submit=False):
    user_query = st.text_area(
        "Enter your natural language question:",
        value=st.session_state.current_query,
        height=85,
        placeholder="e.g. Which department has the largest project budget?"
    )
    submit_button = st.form_submit_button("⚡ Run Query Pipeline", use_container_width=True, type="primary")

if submit_button and user_query.strip():
    st.session_state.current_query = user_query.strip()
    
    with st.spinner("Processing via LangGraph (Schema Mapping -> SQL Generation -> Safety Validation -> Execution)..."):
        result = agent.run(user_query.strip())
    
    # Add to history
    st.session_state.history.insert(0, {
        "question": user_query.strip(),
        "sql": result.get("generated_sql", ""),
        "is_valid": result.get("is_valid", False),
        "row_count": result.get("row_count", 0),
        "execution_time_ms": result.get("execution_time_ms", 0.0),
        "rows": result.get("rows", [])
    })

    # Display Current Result
    st.markdown("### 📊 Pipeline Execution Results")
    
    if not result.get("is_valid") or result.get("error"):
        st.error(f"⚠️ **Execution Blocked / Error**: {result.get('error')}")
        st.code(result.get("generated_sql", ""), language="sql")
    else:
        # Latency and record metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Execution Latency", f"{result['execution_time_ms']:.2f} ms")
        m2.metric("Records Returned", result["row_count"])
        m3.metric("Security Guardrail", "Passed (SELECT Only)")
        m4.metric("Orchestrator", "LangGraph StateGraph")

        st.markdown("#### 📝 Generated & Executed SQL Query")
        st.code(result["generated_sql"], language="sql")

        # Results Table & Chart
        rows = result.get("rows", [])
        if rows:
            df = pd.DataFrame(rows)
            
            tab_table, tab_chart, tab_summary = st.tabs(["📋 Data Table", "📈 Auto Visualization", "💡 Executive Summary"])
            
            with tab_table:
                st.dataframe(df, use_container_width=True)
                
                # CSV Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )

            with tab_chart:
                # Identify potential numeric and categorical columns
                num_cols = df.select_dtypes(include=['number']).columns.tolist()
                cat_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
                
                if num_cols and cat_cols:
                    x_col = cat_cols[0]
                    y_col = num_cols[0]
                    st.caption(f"Plotting `{y_col}` by `{x_col}`:")
                    st.bar_chart(df.set_index(x_col)[y_col])
                elif len(num_cols) >= 2:
                    st.bar_chart(df[num_cols])
                else:
                    st.info("Chart view is optimized for queries with categorical and numeric metric columns.")

            with tab_summary:
                st.markdown(result["response"])
        else:
            st.warning("No records matched your search criteria.")

# Query History Section
if st.session_state.history:
    st.markdown("---")
    st.subheader("📜 Recent Query History")
    for i, item in enumerate(st.session_state.history[:5]):
        with st.expander(f"Q{i+1}: {item['question']} ({item['row_count']} rows, {item['execution_time_ms']:.2f} ms)"):
            st.code(item["sql"], language="sql")
