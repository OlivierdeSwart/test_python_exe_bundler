import sys
import os
import streamlit as st
import pandas as pd
import io
from report_generator import generate_report

# Add root path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ⬜ Force light mode and improve input visibility
st.markdown("""
    <style>
    body {
        background-color: white !important;
        color: black !important;
    }
    input {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ccc !important;
        border-radius: 0.5rem !important;
        padding: 0.4rem !important;
    }
    .stButton > button {
        border-radius: 0.5rem !important;
        padding: 0.4rem 1rem !important;
    }
    .stTextInput, .stForm {
        border-radius: 0.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# 🗂 Setup paths
data_dir = os.path.join(os.path.dirname(__file__), "../data")
combined_path = os.path.join(data_dir, "combined.csv")
os.makedirs(data_dir, exist_ok=True)

# 📁 Check if dataset exists
if not os.path.exists(combined_path):
    st.title("📤 Upload Required Dataset")
    st.warning("Please manually place a CSV file named `combined.csv` into the `optium_capital-main/data/` folder.")
    st.caption("🔹 Only one CSV file is expected.\n🔹 File must be named `combined.csv`.\n🔹 This is required to run the app.")
    st.stop()

# ✅ Load data
@st.cache_data
def load_data():
    return pd.read_csv(combined_path, dtype={'entity_id': str})

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
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
