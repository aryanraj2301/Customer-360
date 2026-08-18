import streamlit as st
import duckdb
import pandas as pd

con = duckdb.connect("../warehouse/customer360.duckdb")
df = con.execute("SELECT * FROM gold_customer_360").fetchdf()

st.title("Customer 360 Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Total Customers", len(df))
col2.metric("Total Lifetime Value", f"${df['lifetime_value'].sum():,.0f}")
col3.metric("At-Risk Customers", int(df['churn_risk_flag'].sum()))

st.subheader("Customer 360 Table")
st.dataframe(df)

st.subheader("Lifetime Value Distribution")
st.bar_chart(df.set_index("customer_id")["lifetime_value"])