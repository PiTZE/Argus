import streamlit as st
import duckdb
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import glob
import time
from collections import defaultdict
import pandas as pd
from datetime import datetime
import io

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Gharp Search")

# --- Constants ---
CSV_BASE_PATH = 'db/'
DUCKDB_TEMP_DIR = os.path.join(os.getcwd(), 'duckdb_temp')

# --- User Authentication ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("FATAL: config.yaml not found. The application cannot start without it.")
    st.stop()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login()
if st.session_state.get("authentication_status") is False:
    st.error('Username/password is incorrect')
    st.stop()
elif st.session_state.get("authentication_status") is None:
    st.warning('Please enter your username and password to access the application.')
    st.stop()

# --- DuckDB Connection ---
@st.cache_resource
def get_duckdb_connection():
    os.makedirs(DUCKDB_TEMP_DIR, exist_ok=True)
    con = duckdb.connect(read_only=False)
    con.execute("INSTALL icu;")
    con.execute("LOAD icu;")
    con.execute("SET memory_limit = '1.5GB';")
    con.execute(f"SET temp_directory = '{DUCKDB_TEMP_DIR}';")
    return con

con = get_duckdb_connection()

# --- File Analysis Functions ---
@st.cache_data(ttl=600)
def get_file_info(file_path):
    """Get file size and basic info without loading the entire file."""
    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Get row count efficiently using DuckDB
        path_escaped = file_path.replace("'", "''")
        row_count = con.execute(
            f"SELECT COUNT(*) as count FROM read_csv_auto('{path_escaped}', HEADER=TRUE);"
        ).fetchone()[0]
        
        return {
            'size_mb': file_size_mb,
            'row_count': row_count,
            'status': 'healthy' if file_size_mb < 500 else 'large'
        }
    except Exception as e:
        return {'size_mb': 0, 'row_count': 0, 'status': 'error', 'error': str(e)}

# --- Enhanced Metadata Scanning ---
@st.cache_data(ttl=600)
def get_metadata(csv_path: str):
    files = glob.glob(os.path.join(csv_path, '*.csv'))
    columns = defaultdict(list)
    file_stats = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file_path in enumerate(files):
        file_name = os.path.basename(file_path)
        status_text.text(f"Analyzing {file_name}...")
        
        try:
            # Get file statistics
            file_stats[file_path] = get_file_info(file_path)
            
            # Get column schema efficiently
            path_escaped = file_path.replace("'", "''")
            schema = con.execute(
                f"DESCRIBE SELECT * FROM read_csv_auto('{path_escaped}', HEADER=TRUE) LIMIT 0;"
            ).fetchdf()
            for col in schema['column_name']:
                columns[col].append(file_path)
                
        except Exception as e:
            file_stats[file_path] = {'size_mb': 0, 'row_count': 0, 'status': 'error', 'error': str(e)}
            st.warning(f"⚠️ Could not analyze {file_name}: {str(e)}")
            continue
            
        progress_bar.progress((i + 1) / len(files))
    
    progress_bar.empty()
    status_text.empty()
    return columns, files, file_stats

# --- Initialize Session State ---
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# --- Load Data with Enhanced Feedback ---
with st.spinner("🔍 Analyzing CSV files..."):
    all_column_data, csv_files, file_stats = get_metadata(CSV_BASE_PATH)

if not all_column_data:
    st.error(f"No CSV files or columns found in '{CSV_BASE_PATH}'.")
    st.stop()

# --- Data Overview Dashboard ---
def show_data_overview():
    st.subheader("📊 Data Overview")
    
    total_files = len(csv_files)
    total_rows = sum(stats.get('row_count', 0) for stats in file_stats.values())
    total_size_mb = sum(stats.get('size_mb', 0) for stats in file_stats.values())
    unique_columns = len(all_column_data)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 Total Files", total_files)
    with col2:
        st.metric("📊 Total Rows", f"{total_rows:,}")
    with col3:
        st.metric("💾 Total Size", f"{total_size_mb:.1f} MB")
    with col4:
        st.metric("🏷️ Unique Columns", unique_columns)
    
    # File details in expandable section
    with st.expander("📋 File Details"):
        for file_path in csv_files:
            file_name = os.path.basename(file_path)
            stats = file_stats.get(file_path, {})
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                status_icon = "✅" if stats.get('status') == 'healthy' else "⚠️" if stats.get('status') == 'large' else "❌"
                st.write(f"{status_icon} **{file_name}**")
            with col2:
                st.write(f"{stats.get('row_count', 0):,} rows")
            with col3:
                st.write(f"{stats.get('size_mb', 0):.1f} MB")
            with col4:
                if stats.get('status') == 'large':
                    st.write("🐌 Large file")
                elif stats.get('status') == 'error':
                    st.write("❌ Error")
                else:
                    st.write("✅ Ready")

# --- Export Functions ---
def export_dataframe(df, filename_prefix="search_results"):
    """Create export options for search results."""
    if df.empty:
        st.warning("No data to export.")
        return
    
    st.subheader("📥 Export Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV Export
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Excel Export
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Search Results')
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col3:
        # JSON Export
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="🔗 Download JSON",
            data=json_data,
            file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# --- Sidebar Inputs ---
with st.sidebar:
    st.success(f'Welcome *{st.session_state["name"]}*')
    authenticator.logout()

    st.header("🔍 Search Options")
    
    # Column selection with file count
    formatted = [f"{col} (in {len(files)} files)" for col, files in all_column_data.items()]
    selected = st.selectbox("Select column to search:", options=formatted)
    column_name = selected.split(' (in ')[0]
    
    # Show which files contain this column
    files_with_column = all_column_data[column_name]
    with st.expander(f"📁 Files containing '{column_name}' ({len(files_with_column)})"):
        for file_path in files_with_column:
            file_name = os.path.basename(file_path)
            stats = file_stats.get(file_path, {})
            size_mb = stats.get('size_mb', 0)
            row_count = stats.get('row_count', 0)
            st.write(f"• **{file_name}** ({row_count:,} rows, {size_mb:.1f} MB)")

    # Enhanced search options
    search_term = st.text_input("🔎 Search term:", help="Enter text to search for in the selected column")
    
    # Search type selection
    search_type = st.selectbox(
        "Search type:",
        ["Contains (case-insensitive)", "Exact match", "Starts with", "Ends with"],
        help="Choose how to match your search term"
    )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        result_limit = st.number_input(
            "Max rows per file:", min_value=5, max_value=10000, value=100, step=25,
            help="Limit results to prevent memory issues with large files"
        )
        
        # File size warning
        large_files = [f for f, stats in file_stats.items() if stats.get('size_mb', 0) > 100]
        if large_files:
            st.warning(f"⚠️ {len(large_files)} large files detected. Consider using smaller result limits.")
    
    search_button = st.button("🚀 Search", type="primary")
    
    # Search History
    if st.session_state.search_history:
        st.header("📚 Recent Searches")
        for i, search in enumerate(reversed(st.session_state.search_history[-5:])):  # Show last 5
            if st.button(f"🔄 {search['term']} in {search['column']}", key=f"history_{i}"):
                st.session_state.search_term_from_history = search['term']
                st.session_state.column_from_history = search['column']
                st.rerun()

# --- Main Content Area ---
# Show data overview first
show_data_overview()

# --- Enhanced Search Execution ---
def build_search_query(search_term, search_type, column_name):
    """Build the appropriate SQL query based on search type."""
    if search_type == "Exact match":
        return f'"{column_name}"::VARCHAR = ?', [search_term]
    elif search_type == "Starts with":
        return f'"{column_name}"::VARCHAR ILIKE ?', [f"{search_term}%"]
    elif search_type == "Ends with":
        return f'"{column_name}"::VARCHAR ILIKE ?', [f"%{search_term}"]
    else:  # Contains (case-insensitive)
        return f'"{column_name}"::VARCHAR ILIKE ?', [f"%{search_term}%"]

if search_button:
    if not search_term:
        st.warning("⚠️ Please enter a search term.")
    else:
        # Add to search history
        search_entry = {
            'term': search_term,
            'column': column_name,
            'timestamp': datetime.now(),
            'type': search_type
        }
        st.session_state.search_history.append(search_entry)
        
        files_to_search = all_column_data.get(column_name, [])
        if not files_to_search:
            st.error("❌ No files contain the selected column.")
        else:
            st.header("🔍 Search Results")
            
            # Search summary
            total_files = len(files_to_search)
            total_size = sum(file_stats.get(f, {}).get('size_mb', 0) for f in files_to_search)
            st.info(f"🎯 Searching **{total_files}** files ({total_size:.1f} MB total) for **'{search_term}'** in column **'{column_name}'** using **{search_type.lower()}**")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()
            
            all_results = []
            found_any = False
            start_time = time.time()
            
            # Build search query
            where_clause, params = build_search_query(search_term, search_type, column_name)

            for idx, file_path in enumerate(files_to_search, start=1):
                file_name = os.path.basename(file_path)
                file_size = file_stats.get(file_path, {}).get('size_mb', 0)
                
                status_text.info(f"🔍 Searching file {idx}/{total_files}: **{file_name}** ({file_size:.1f} MB)")
                
                try:
                    clean_path = file_path.replace("'", "''")
                    query = f"""
                        SELECT *
                        FROM read_csv_auto('{clean_path}', HEADER=TRUE, IGNORE_ERRORS=TRUE)
                        WHERE {where_clause}
                        LIMIT {result_limit};
                    """
                    
                    # Execute query with timeout protection for large files
                    df = con.execute(query, params).fetchdf()
                    
                    if not df.empty:
                        found_any = True
                        all_results.append(df)
                        
                        with results_container:
                            st.subheader(f"📄 Results from: {file_name}")
                            st.caption(f"Found {len(df):,} matches (showing max {result_limit:,} rows)")
                            st.dataframe(df, use_container_width=True)
                            
                            # Export individual file results
                            if len(df) > 0:
                                export_dataframe(df, f"{file_name.replace('.csv', '')}_results")
                            
                            st.divider()
                            
                except Exception as e:
                    error_msg = str(e)
                    if "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
                        st.error(f"💾 **Memory Error** in {file_name}: File too large. Try reducing result limit or use a more specific search.")
                    else:
                        st.warning(f"⚠️ **Skipped** {file_name}: {error_msg}")
                
                progress_bar.progress(idx / total_files)

            # Final results summary
            duration = time.time() - start_time
            progress_bar.empty()
            
            if found_any:
                # Combine all results for bulk export
                if len(all_results) > 1:
                    combined_df = pd.concat(all_results, ignore_index=True)
                    st.success(f"✅ **Search completed** in {duration:.2f} seconds. Found results in {len(all_results)} files.")
                    
                    # Export all combined results
                    st.subheader("📦 Export All Results")
                    export_dataframe(combined_df, "combined_search_results")
                else:
                    st.success(f"✅ **Search completed** in {duration:.2f} seconds.")
                    
                status_text.success(f"🎉 Search finished! Found {sum(len(df) for df in all_results):,} total matches.")
            else:
                status_text.info(f"🔍 Search completed in {duration:.2f} seconds - No matches found.")
                st.info("💡 **No results found.** Try:\n- Using a different search type\n- Checking spelling\n- Using partial terms\n- Selecting a different column")