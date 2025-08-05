import streamlit as st
import duckdb
import os
import glob
from config import load_config, configure_duckdb, get_directories

config = load_config()
dirs = get_directories(config)
PARQUET_DIR = dirs['output_dir']

st.title("Argus 👁👁")

con = duckdb.connect()
configure_duckdb(con, config)
parquet_files = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))

def get_file_schema(file_path):
    """Get column schema for a parquet file"""
    try:
        result = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path}')").fetchall()
        return {col[0]: col[1] for col in result}
    except:
        return {}

def group_files_by_schema(files):
    """Group files by compatible column schemas"""
    groups = {}
    for file_path in files:
        schema = get_file_schema(file_path)
        if not schema:
            continue
            
        schema_key = tuple(sorted(schema.keys()))
        
        group_name = None
        for existing_group, existing_files in groups.items():
            if existing_files and schema_key == tuple(sorted(get_file_schema(existing_files[0]).keys())):
                group_name = existing_group
                break
        
        if group_name is None:
            group_name = f"Schema {len(groups) + 1} ({len(schema)} columns)"
            groups[group_name] = []
        
        groups[group_name].append(file_path)
    
    return groups

def create_union_query(selected_files):
    """Create UNION ALL query with proper aliases"""
    if len(selected_files) == 1:
        return f"read_parquet('{selected_files[0]}')"
    
    union_parts = []
    for i, file_path in enumerate(selected_files):
        alias = f"t{i}"
        union_parts.append(f"SELECT * FROM read_parquet('{file_path}') AS {alias}")
    
    return f"({' UNION ALL '.join(union_parts)})"

if not parquet_files:
    st.error("No Parquet files found.")
else:
    file_groups = group_files_by_schema(parquet_files)
    
    if not file_groups:
        st.error("No valid parquet files found.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            selected_group = st.selectbox(
                "Schema Group:",
                options=list(file_groups.keys())
            )
        
        with col2:
            available_files = file_groups[selected_group]
            max_files = st.slider(
                "Files to use:",
                min_value=1,
                max_value=len(available_files),
                value=min(3, len(available_files))
            )
        
        selected_files = available_files[:max_files]
        
        with col3:
            try:
                table_expr = create_union_query(selected_files)
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
        
        with col4:
            query = st.text_input("Search for:", "")
        
        st.write(f"**Selected files ({len(selected_files)}):**")
        for f in selected_files:
            filename = os.path.basename(f).replace('.parquet', '')
            st.write(f"• {filename}")
        
        if query:
            st.write(f"Searching in: **{len(selected_files)} files** | Column: **{selected_column}** | Query: `{query}`")
            
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
