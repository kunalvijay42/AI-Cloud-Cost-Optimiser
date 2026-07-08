from __future__ import annotations

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


st.set_page_config(page_title="AI Cloud Cost Optimiser", layout="wide")
st.title("AI Cloud Cost Optimiser")
st.caption("Upload a cloud billing export and get AI-powered cost-saving suggestions")

with st.sidebar:
    st.header("Upload billing export")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    analyze_button = st.button("Analyze")

if analyze_button and uploaded_file is not None:
    with st.spinner("Analyzing the billing export..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/analyze",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            st.error(f"The backend request failed: {exc}")
            st.stop()

    st.success(f"Analysis complete for {data.get('provider', 'unknown')} billing data")

    stats = data.get("stats", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Total cost", f"${stats.get('total_cost', 0):,.2f}")
    col2.metric("Records", stats.get("total_records", 0))
    col3.metric("Provider", data.get("provider", "unknown"))

    service_costs = stats.get("cost_by_service", {})
    if service_costs:
        st.subheader("Cost by service")
        st.bar_chart(service_costs)

    top_expenses = stats.get("top_expenses", [])
    if top_expenses:
        st.subheader("Top expenses")
        st.dataframe(top_expenses)

    st.subheader("AI suggestions")
    suggestions = data.get("suggestions", [])
    if suggestions:
        for suggestion in suggestions:
            with st.container():
                priority = str(suggestion.get("priority", "medium")).upper()
                st.markdown(f"### {priority} PRIORITY")
                st.markdown(f"**Recommendation:** {suggestion.get('suggestion', '')}")
                st.write(f"Affected resource: {suggestion.get('affected_resource', 'unknown')}")
                st.write(
                    f"Estimated monthly savings: ${suggestion.get('estimated_monthly_savings', 0):,.2f}"
                )
                st.divider()
    else:
        st.info("No suggestions were returned by the backend.")
else:
    st.info("Upload a CSV file and press Analyze to begin.")
