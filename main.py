import streamlit as st
import duckdb
import os
import glob

PARQUET_DIR = "data/parq"

st.title("Argus 👁👁")

con = duckdb.connect()
con.execute("SET memory_limit='256MB'")
con.execute("SET threads=1")
con.execute("SET max_memory='256MB'")
con.execute("SET temp_directory='/tmp'")
parquet_files = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))

if not parquet_files:
    st.error("No Parquet files found.")
else:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_file = st.selectbox(
            "File:",
            options=["All files"] + [os.path.basename(f) for f in parquet_files]
        )
    
    with col2:
        if selected_file == "All files":
            table_expr = ", ".join([f"read_parquet('{f}')" for f in parquet_files])
        else:
            selected_path = next(f for f in parquet_files if os.path.basename(f) == selected_file)
            table_expr = f"read_parquet('{selected_path}')"
        
        try:
            columns_query = f"DESCRIBE SELECT * FROM {table_expr}"
            columns_result = con.execute(columns_query).fetchall()
            column_names = [col[0] for col in columns_result]
            
            selected_column = st.selectbox(
                "Column:",
                options=["All columns"] + column_names
            )
        except Exception as e:
            st.error(f"Error getting columns: {e}")
            selected_column = "All columns"
            column_names = []
    
    with col3:
        query = st.text_input("Search for:", "")
    
    if query:
        st.write(f"Searching in: **{selected_file}** | Column: **{selected_column}** | Query: `{query}`")
        
        try:
            if selected_column == "All columns":
                where_conditions = []
                for col_name in column_names:
                    where_conditions.append(f"CAST({col_name} AS VARCHAR) ILIKE '%{query}%'")
                where_clause = " OR ".join(where_conditions) if where_conditions else "1=0"
            else:
                where_clause = f"CAST({selected_column} AS VARCHAR) ILIKE '%{query}%'"
            
            duck_query = f"""
            SELECT * FROM {table_expr}
            WHERE {where_clause}
            LIMIT 100
            """
            
            result = con.execute(duck_query).fetchdf()
            st.dataframe(result)
            
        except Exception as e:
            st.error(f"Query failed: {e}")
