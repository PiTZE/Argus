import streamlit as st
import duckdb
import os
import glob

PARQUET_DIR = "data/parq"

st.title("Argus 👁👁")
query = st.text_input("Search for:", "")

if query:
    st.write(f"Showing results for: `{query}`")

    con = duckdb.connect()

    parquet_files = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))
    if not parquet_files:
        st.error("No Parquet files found.")
    else:
        table_expr = ", ".join([f"read_parquet('{f}')" for f in parquet_files])
        duck_query = f"""
        SELECT * FROM {table_expr}
        WHERE
            CAST(id AS VARCHAR) ILIKE '%{query}%'
            OR name ILIKE '%{query}%'
            OR CAST(score AS VARCHAR) ILIKE '%{query}%'
            OR CAST(category AS VARCHAR) ILIKE '%{query}%'
        LIMIT 100
        """
        try:
            result = con.execute(duck_query).fetchdf()
            st.dataframe(result)
        except Exception as e:
            st.error(f"Query failed: {e}")
