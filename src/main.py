import streamlit as st
import duckdb
import os
import glob
import time
from config import load_config, configure_duckdb, get_directories

# ============================================================================
# CONFIGURATION AND INITIALIZATION
# ============================================================================

config = load_config()
dirs = get_directories(config)
PARQUET_DIR = dirs['output_dir']

st.set_page_config(
    page_title="Argus",
    page_icon="👁",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Argus 👁👁")

# Initialize database connection
con = duckdb.connect()
configure_duckdb(con, config)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_file_schema(file_path):
    """Get column schema for a parquet file"""
    try:
        result = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path}')").fetchall()
        return {col[0]: col[1] for col in result}
    except:
        return {}

def get_file_stats(file_path):
    """Get basic statistics for a parquet file"""
    try:
        # Get row count
        row_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{file_path}')").fetchone()[0]
        
        # Get file size
        file_size = os.path.getsize(file_path)
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        # Get column count
        schema = get_file_schema(file_path)
        col_count = len(schema)
        
        return {
            'rows': row_count,
            'size': size_str,
            'columns': col_count
        }
    except:
        return {'rows': 0, 'size': '0 B', 'columns': 0}

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
            # Extract common name pattern from files
            filename = os.path.basename(file_path).replace('.parquet', '')
            # Remove numbers and common suffixes to find base name
            import re
            base_name = re.sub(r'\d+$', '', filename).rstrip('_-')
            
            # Check if this base name already exists
            existing_base_names = []
            for existing_group in groups.keys():
                if not existing_group.startswith("Schema"):
                    existing_base_names.append(existing_group)
            
            if base_name and base_name not in existing_base_names:
                group_name = base_name
            else:
                group_name = f"Schema {len(groups) + 1} ({len(schema)} columns)"
            
            groups[group_name] = []
        
        groups[group_name].append(file_path)
    
    return groups

def create_union_query(selected_files):
    """Create UNION ALL query with proper aliases and source file column"""
    if len(selected_files) == 1:
        filename = os.path.basename(selected_files[0]).replace('.parquet', '')
        return f"SELECT *, '{filename}' AS _source_file FROM read_parquet('{selected_files[0]}')"
    
    union_parts = []
    for i, file_path in enumerate(selected_files):
        alias = f"t{i}"
        filename = os.path.basename(file_path).replace('.parquet', '')
        union_parts.append(f"SELECT *, '{filename}' AS _source_file FROM read_parquet('{file_path}') AS {alias}")
    
    return f"({' UNION ALL '.join(union_parts)})"

# ============================================================================
# DATA LOADING AND PROCESSING
# ============================================================================

# Load parquet files with loading indicator
with st.spinner("Loading parquet files..."):
    parquet_files = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))

if not parquet_files:
    st.error("No Parquet files found.")
    st.stop()

# Group files by schema with loading indicator
with st.spinner("Analyzing file schemas..."):
    file_groups = group_files_by_schema(parquet_files)

if not file_groups:
    st.error("No valid parquet files found.")
    st.stop()

# ============================================================================
# METRICS DASHBOARD
# ============================================================================

# Calculate total statistics
total_files = len(parquet_files)
total_groups = len(file_groups)

# Calculate total rows and size
with st.spinner("Calculating statistics..."):
    total_rows = 0
    total_size_bytes = 0
    
    progress_bar = st.progress(0)
    for i, file_path in enumerate(parquet_files):
        stats = get_file_stats(file_path)
        total_rows += stats['rows']
        total_size_bytes += os.path.getsize(file_path)
        progress_bar.progress((i + 1) / len(parquet_files))
    
    progress_bar.empty()

# Format total size
if total_size_bytes < 1024 * 1024:
    total_size = f"{total_size_bytes / 1024:.1f} KB"
elif total_size_bytes < 1024 * 1024 * 1024:
    total_size = f"{total_size_bytes / (1024 * 1024):.1f} MB"
else:
    total_size = f"{total_size_bytes / (1024 * 1024 * 1024):.1f} GB"

# Display metrics dashboard
st.subheader("Data Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Files", total_files)

with col2:
    st.metric("Schema Groups", total_groups)

with col3:
    st.metric("Total Rows", f"{total_rows:,}")

with col4:
    st.metric("Total Size", total_size)

st.divider()

# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================

with st.sidebar:
    st.header("Search Controls")
    
    # Schema group selection
    selected_group = st.selectbox(
        "Schema Group:",
        options=list(file_groups.keys()),
        help="Select a group of files with compatible schemas"
    )
    
    available_files = file_groups[selected_group]
    selected_files = available_files
    
    # Column selection
    try:
        with st.spinner("Loading column information..."):
            table_expr = create_union_query(selected_files)
            columns_query = f"DESCRIBE SELECT * FROM {table_expr}"
            columns_result = con.execute(columns_query).fetchall()
            column_names = [col[0] for col in columns_result if col[0] != '_source_file']
        
        selected_column = st.selectbox(
            "Column:",
            options=["All columns"] + column_names,
            help="Select a specific column to search in, or search all columns"
        )
    except Exception as e:
        st.error(f"Error getting columns: {e}")
        selected_column = "All columns"
        column_names = []
    
    # Search query
    query = st.text_input(
        "Search for:",
        placeholder="Enter search term...",
        help="Search for text in the selected column(s)"
    )
    
    # Search button
    search_clicked = st.button(
        "Search",
        use_container_width=True,
        help="Click to execute the search",
        disabled=not query.strip()  # Disable if query is empty
    )
    
    # Pagination settings
    st.subheader("Settings")
    rows_per_page = st.number_input(
        "Rows per page:",
        min_value=10,
        max_value=1000,
        value=100,
        step=10,
        help="Number of rows to display per page"
    )
    
    # Cache management
    st.subheader("Cache")
    if st.button("Clear Cache", help="Clear cached results and refresh data"):
        # Clear all cache-related session state
        for key in ['cached_results', 'cached_total_rows', 'cache_key']:
            if key in st.session_state:
                del st.session_state[key]
        if 'current_page' in st.session_state:
            st.session_state.current_page = 1
        st.rerun()
    
    # Show cache status
    if 'cached_results' in st.session_state:
        cache_size = len(st.session_state.cached_results)
        st.caption(f"Cached: {cache_size:,} results")

# ============================================================================
# FILE INFORMATION DISPLAY
# ============================================================================

st.subheader(f"Selected Files ({len(selected_files)})")

# Display file information in an expandable section
with st.expander("View file details", expanded=False):
    for file_path in selected_files:
        filename = os.path.basename(file_path).replace('.parquet', '')
        stats = get_file_stats(file_path)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write(f"**{filename}**")
        with col2:
            st.write(f"Rows: {stats['rows']:,}")
        with col3:
            st.write(f"Size: {stats['size']}")
        with col4:
            st.write(f"Columns: {stats['columns']}")

# ============================================================================
# SEARCH AND RESULTS WITH CACHING
# ============================================================================

if query and search_clicked:
    st.subheader("Search Results")
    
    # Display search information
    search_info = f"Searching in **{len(selected_files)} files** | Column: **{selected_column}** | Query: `{query}`"
    st.info(search_info)
    
    try:
        # Create cache key from search parameters
        cache_key = f"{selected_group}_{selected_column}_{query}_{len(selected_files)}"
        
        # Check if we need to invalidate cache
        cache_invalid = (
            'cache_key' not in st.session_state or
            st.session_state.cache_key != cache_key or
            'cached_results' not in st.session_state
        )
        
        if cache_invalid:
            # Clear old cache and reset pagination
            for key in ['cached_results', 'cached_total_rows']:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.cache_key = cache_key
            st.session_state.current_page = 1
            
            # Build where clause
            with st.spinner("Building search query..."):
                if selected_column == "All columns":
                    where_conditions = []
                    for col_name in column_names:
                        where_conditions.append(f"CAST({col_name} AS VARCHAR) ILIKE '%{query}%'")
                    where_clause = " OR ".join(where_conditions) if where_conditions else "1=0"
                else:
                    where_clause = f"CAST({selected_column} AS VARCHAR) ILIKE '%{query}%'"
            
            # Execute full query and cache results
            full_query = f"""
            SELECT * FROM {table_expr}
            WHERE {where_clause}
            ORDER BY _source_file
            """
            
            with st.spinner("Executing search query and caching results..."):
                start_time = time.time()
                cached_results = con.execute(full_query).fetchdf()
                query_time = time.time() - start_time
                
                # Store in session state
                st.session_state.cached_results = cached_results
                st.session_state.cached_total_rows = len(cached_results)
                st.session_state.query_time = query_time
            
            st.success(f"Query executed and cached in {query_time:.3f} seconds")
        
        # Get cached results
        cached_results = st.session_state.cached_results
        total_rows = st.session_state.cached_total_rows
        
        if total_rows == 0:
            st.info("No results found.")
        else:
            # Initialize session state for pagination
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
            
            # Calculate pagination
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page
            
            # Ensure current page is within bounds
            if st.session_state.current_page > total_pages:
                st.session_state.current_page = total_pages
            if st.session_state.current_page < 1:
                st.session_state.current_page = 1
            
            # Results summary with cache info
            cache_indicator = "Cached" if not cache_invalid else "Nope"
            st.write(f"**Found {total_rows:,} results** (Page {st.session_state.current_page} of {total_pages}) {cache_indicator}")
            
            # Pagination controls with better layout
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮ First", disabled=st.session_state.current_page <= 1, use_container_width=True):
                    st.session_state.current_page = 1
                    st.rerun()
            
            with col2:
                if st.button("◀ Prev", disabled=st.session_state.current_page <= 1, use_container_width=True):
                    st.session_state.current_page = max(1, st.session_state.current_page - 1)
                    st.rerun()
            
            with col3:
                current_page = st.number_input(
                    "Go to page:",
                    min_value=1,
                    max_value=total_pages,
                    value=st.session_state.current_page,
                    key='page_input',
                    help=f"Enter page number (1-{total_pages})"
                )
                if current_page != st.session_state.current_page:
                    st.session_state.current_page = current_page
                    st.rerun()
            
            with col4:
                if st.button("Next ▶", disabled=st.session_state.current_page >= total_pages, use_container_width=True):
                    st.session_state.current_page = min(total_pages, st.session_state.current_page + 1)
                    st.rerun()
            
            with col5:
                if st.button("Last ⏭", disabled=st.session_state.current_page >= total_pages, use_container_width=True):
                    st.session_state.current_page = total_pages
                    st.rerun()
            
            # Get paginated results from cache (instant!)
            start_idx = (st.session_state.current_page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            paginated_results = cached_results.iloc[start_idx:end_idx]
            
            # Display performance info
            if hasattr(st.session_state, 'query_time'):
                if cache_invalid:
                    st.caption(f"⚡ Initial query: {st.session_state.query_time:.3f}s | Pagination: instant (cached)")
                else:
                    st.caption(f"⚡ Pagination: instant (using cached results from {st.session_state.query_time:.3f}s query)")
            
            # Display results
            st.dataframe(paginated_results, use_container_width=True)
            
            # Memory usage warning for large result sets
            if total_rows > 50000:
                st.warning(f"Large result set ({total_rows:,} rows) cached in memory. Consider refining your search for better performance.")
        
    except Exception as e:
        st.error(f"Query failed: {e}")
        st.error("Please check your search query and try again.")

else:
    if query.strip():
        st.info("Click the Search button to execute your search.")
    else:
        st.info("Enter a search term in the sidebar and click the Search button to begin searching.")
