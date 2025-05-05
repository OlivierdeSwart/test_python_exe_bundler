import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import io
from app.report_generator import generate_report

# ✅ Cache data load for better performance
@st.cache_data
def load_data():
    return pd.read_csv('data/combined.csv', dtype={'entity_id': str})

# Load combined dataset once
try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ Combined data file not found at 'data/combined.csv'. Please run the combine script first.")
    st.stop()

# ✅ App title
st.title("Franchisee Financial Report 2005–2019")

# 🔁 Session state
if 'report' not in st.session_state:
    st.session_state.report = None
if 'last_input' not in st.session_state:
    st.session_state.last_input = ""
if 'monthly_report' not in st.session_state:
    st.session_state.monthly_report = None

# 🔎 Search form
with st.form("search_form", clear_on_submit=False):
    entity_input = st.text_input("Enter ENTITY_IDs separated by commas:", value=st.session_state.last_input)
    submitted = st.form_submit_button("Search")

# 🧮 Handle search
if submitted:
    ids = [e.strip() for e in entity_input.split(",") if e.strip()]
    st.session_state.report = generate_report(df, ids)
    st.session_state.last_input = entity_input
    st.session_state.monthly_report = None

# 📊 Show report
if st.session_state.report is not None:
    st.dataframe(st.session_state.report)

    # 📥 Download main report
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        st.session_state.report.to_excel(writer, index=True, sheet_name='Summary')
    st.download_button(
        label="📄 Download Report (Excel)",
        data=buffer.getvalue(),
        file_name="financial_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 📆 Monthly breakdown toggle
    if 'month' in df.columns:
        show_monthly = st.checkbox("📊 Show month-by-month breakdown", key="show_months")

        if show_monthly:
            ids = [e.strip() for e in st.session_state.last_input.split(",") if e.strip()]
            monthly = df[df['entity_id'].isin(ids)].groupby(['entity_id', 'month'])[
                ['visa fees', 'mastercard fees', 'visa sales', 'mastercard sales']
            ].sum().reset_index()

            st.session_state.monthly_report = monthly
            st.subheader("Monthly Breakdown")
            st.dataframe(monthly)

            if not monthly.empty:
                monthly_buffer = io.BytesIO()
                with pd.ExcelWriter(monthly_buffer, engine='xlsxwriter') as writer:
                    monthly.to_excel(writer, index=False, sheet_name='Monthly Breakdown')
                st.download_button(
                    label="📄 Download Monthly Breakdown (Excel)",
                    data=monthly_buffer.getvalue(),
                    file_name="monthly_breakdown.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# 🧾 Show load count
st.caption(f"{len(df):,} rows loaded from combined dataset.")