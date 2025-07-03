"""Search interface and results display components."""

import streamlit as st
import pandas as pd
import time
import logging
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
from src.database.file_processor import file_processor
from src.database.search_engine import search_engine
from src.ui.export_utils import ExportManager
from src.core.config import config

logger = logging.getLogger(__name__)

class SearchInterface:
    """Advanced search interface for large CSV files."""
    
    def __init__(self):
        self.export_manager = ExportManager()
    
    def render_search_sidebar(self, user_name: str) -> Dict[str, Any]:
        """Render search options in sidebar."""
        with st.sidebar:
            st.header("🔍 Search Configuration")
            
            # Get column distribution
            column_distribution = file_processor.get_column_distribution()
            
            if not column_distribution:
                st.warning("⚠️ No processed files found. Please upload CSV files first.")
                return {}
            
            # Column selection
            formatted_columns = [
                f"{col} (in {len(files)} files)" 
                for col, files in column_distribution.items()
            ]
            
            selected_formatted = st.selectbox(
                "Select column to search:",
                options=formatted_columns,
                help="Choose which column to search across all files"
            )
            
            if not selected_formatted:
                return {}
            
            column_name = selected_formatted.split(' (in ')[0]
            files_with_column = column_distribution[column_name]
            
            # Show files containing this column
            with st.expander(f"📁 Files with '{column_name}' ({len(files_with_column)})"):
                metadata_df = file_processor.get_all_file_metadata()
                
                for file_path in files_with_column:
                    file_info = metadata_df[metadata_df['file_path'] == file_path]
                    if not file_info.empty:
                        info = file_info.iloc[0]
                        st.write(
                            f"• **{info['file_name']}** "
                            f"({info['row_count']:,} rows, {info['file_size_mb']:.1f} MB)"
                        )
            
            # Search term input
            search_term = st.text_input(
                "🔎 Search term:",
                help="Enter text to search for in the selected column",
                key="search_term_input"
            )
            
            # Search type selection
            search_type = st.selectbox(
                "Search type:",
                ["Contains (case-insensitive)", "Exact match", "Starts with", "Ends with", "Regex"],
                help="Choose how to match your search term"
            )
            
            # Advanced options
            with st.expander("⚙️ Advanced Options"):
                # Result limits
                col1, col2 = st.columns(2)
                
                with col1:
                    result_limit = st.number_input(
                        "Max rows per file:",
                        min_value=10,
                        max_value=config.search.max_result_limit,
                        value=config.search.default_page_size,
                        step=50,
                        help="Limit results to prevent memory issues"
                    )
                
                with col2:
                    chunk_size = st.number_input(
                        "Chunk size:",
                        min_value=100,
                        max_value=5000,
                        value=config.search.default_chunk_size,
                        step=100,
                        help="Size of data chunks for processing"
                    )
                
                # Performance options
                use_streaming = st.checkbox(
                    "Enable streaming results",
                    value=True,
                    help="Stream results for better performance with large datasets"
                )
                
                parallel_search = st.checkbox(
                    "Parallel file processing",
                    value=True,
                    help="Search multiple files simultaneously"
                )
                
                # File size warnings
                large_files = []
                metadata_df = file_processor.get_all_file_metadata()
                for file_path in files_with_column:
                    file_info = metadata_df[metadata_df['file_path'] == file_path]
                    if not file_info.empty and file_info.iloc[0]['file_size_mb'] > config.search.large_file_threshold_mb:
                        large_files.append(file_info.iloc[0]['file_name'])
                
                if large_files:
                    st.warning(
                        f"⚠️ Large files detected: {', '.join(large_files[:3])}"
                        f"{'...' if len(large_files) > 3 else ''}. "
                        f"Consider using smaller result limits."
                    )
            
            # Search button
            search_button = st.button("🚀 Search", type="primary", use_container_width=True)
            
            # Recent searches
            self._render_search_history(user_name)
            
            return {
                'column_name': column_name,
                'search_term': search_term,
                'search_type': search_type,
                'result_limit': result_limit,
                'chunk_size': chunk_size,
                'use_streaming': use_streaming,
                'parallel_search': parallel_search,
                'files_with_column': files_with_column,
                'search_button': search_button
            }
    
    def _render_search_history(self, user_name: str):
        """Render search history in sidebar."""
        try:
            recent_searches = search_engine.get_search_history(user_name, limit=5)
            
            if not recent_searches.empty:
                st.header("📚 Recent Searches")
                
                for i, search in recent_searches.iterrows():
                    search_label = f"🔄 {search['search_term'][:20]}{'...' if len(search['search_term']) > 20 else ''}"
                    search_details = f"in {search['column_name']} ({search['results_found']:,} results)"
                    
                    if st.button(
                        f"{search_label}\n{search_details}",
                        key=f"history_{i}",
                        help=f"Search: {search['search_term']}\nColumn: {search['column_name']}\nType: {search['search_type']}"
                    ):
                        # Set session state to reuse search
                        st.session_state.search_term_input = search['search_term']
                        st.rerun()
                        
        except Exception as e:
            logger.error(f"Error rendering search history: {e}")
    
    def execute_search(self, search_params: Dict[str, Any], user_name: str):
        """Execute search with progress tracking and results display."""
        if not search_params.get('search_term'):
            st.warning("⚠️ Please enter a search term.")
            return
        
        # Extract parameters
        search_term = search_params['search_term']
        column_name = search_params['column_name']
        search_type = search_params['search_type']
        files_with_column = search_params['files_with_column']
        result_limit = search_params['result_limit']
        use_streaming = search_params['use_streaming']
        parallel_search = search_params['parallel_search']
        
        st.header("🔍 Search Results")
        
        # Search summary
        total_files = len(files_with_column)
        metadata_df = file_processor.get_all_file_metadata()
        total_size = sum(
            metadata_df[metadata_df['file_path'] == f]['file_size_mb'].iloc[0] 
            if not metadata_df[metadata_df['file_path'] == f].empty else 0
            for f in files_with_column
        )
        
        st.info(
            f"🎯 Searching **{total_files}** files ({total_size:.1f} MB total) "
            f"for **'{search_term}'** in column **'{column_name}'** "
            f"using **{search_type.lower()}**"
        )
        
        # Progress tracking
        progress_container = st.container()
        results_container = st.container()
        
        start_time = time.time()
        
        try:
            if parallel_search and len(files_with_column) > 1:
                # Parallel search
                self._execute_parallel_search(
                    files_with_column, search_term, search_type, column_name,
                    result_limit, progress_container, results_container, user_name
                )
            else:
                # Sequential search
                self._execute_sequential_search(
                    files_with_column, search_term, search_type, column_name,
                    result_limit, use_streaming, progress_container, results_container, user_name
                )
                
        except Exception as e:
            logger.error(f"Search execution error: {e}")
            st.error(f"❌ Search failed: {e}")
    
    def _execute_parallel_search(self, files_with_column: List[str], search_term: str,
                                search_type: str, column_name: str, result_limit: int,
                                progress_container, results_container, user_name: str):
        """Execute parallel search across multiple files."""
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.info("🚀 Starting parallel search...")
        
        # Execute parallel search
        search_results = search_engine.search_multiple_files(
            files_with_column, search_term, search_type, column_name, result_limit
        )
        
        progress_bar.progress(1.0)
        
        # Display results
        self._display_search_results(search_results, results_container, user_name)
        
        # Save to history
        total_results = search_results.get('total_results', 0)
        duration_ms = int(search_results.get('total_duration', 0) * 1000)
        
        search_engine.save_search_history(
            user_name, search_term, column_name, search_type,
            len(files_with_column), total_results, duration_ms
        )
        
        with progress_container:
            status_text.success(
                f"✅ Parallel search completed in {search_results.get('total_duration', 0):.2f}s. "
                f"Found {total_results:,} total results."
            )
    
    def _execute_sequential_search(self, files_with_column: List[str], search_term: str,
                                  search_type: str, column_name: str, result_limit: int,
                                  use_streaming: bool, progress_container, results_container, user_name: str):
        """Execute sequential search with optional streaming."""
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        all_results = []
        total_results = 0
        
        for idx, file_path in enumerate(files_with_column, 1):
            file_name = os.path.basename(file_path)
            
            with progress_container:
                status_text.info(f"🔍 Searching file {idx}/{len(files_with_column)}: **{file_name}**")
                progress_bar.progress(idx / len(files_with_column))
            
            try:
                if use_streaming:
                    # Stream results for large files
                    result_generator = search_engine.stream_search_results(
                        file_path, search_term, search_type, column_name
                    )
                    
                    file_results = []
                    for chunk in result_generator:
                        if isinstance(chunk, pd.DataFrame):
                            file_results.append(chunk)
                    
                    if file_results:
                        combined_df = pd.concat(file_results, ignore_index=True)
                        self._display_file_results(combined_df, file_name, results_container)
                        all_results.append(combined_df)
                        total_results += len(combined_df)
                else:
                    # Regular search
                    result_df, metadata = search_engine.search_single_file(
                        file_path, search_term, search_type, column_name, result_limit
                    )
                    
                    if result_df is not None and not result_df.empty:
                        self._display_file_results(result_df, file_name, results_container)
                        all_results.append(result_df)
                        total_results += len(result_df)
                        
            except Exception as e:
                logger.error(f"Error searching {file_path}: {e}")
                with results_container:
                    st.error(f"❌ Error searching {file_name}: {e}")
        
        # Final summary and export options
        if all_results:
            with results_container:
                st.success(f"✅ Search completed. Found {total_results:,} total results.")
                
                # Combined export
                if len(all_results) > 1:
                    combined_df = pd.concat(all_results, ignore_index=True)
                    st.subheader("📦 Export All Results")
                    self.export_manager.render_export_options(combined_df, "combined_search_results")
        
        # Save to history
        duration_ms = int((time.time() - time.time()) * 1000)  # Approximate
        search_engine.save_search_history(
            user_name, search_term, column_name, search_type,
            len(files_with_column), total_results, duration_ms
        )
    
    def _display_search_results(self, search_results: Dict[str, Any], results_container, user_name: str):
        """Display parallel search results."""
        
        if search_results.get('cached'):
            with results_container:
                st.info("⚡ Using cached results for faster response")
                cache_info = search_results['cache_info']
                st.write(f"Results: {cache_info['result_count']:,}, "
                        f"Original execution time: {cache_info['execution_time_ms']/1000:.2f}s")
            return
        
        results = search_results.get('results', {})
        all_results = []
        
        with results_container:
            for file_path, file_result in results.items():
                file_name = file_result['file_name']
                result_df = file_result['data']
                metadata = file_result['metadata']
                
                if result_df is not None and not result_df.empty:
                    self._display_file_results(result_df, file_name, st.container())
                    all_results.append(result_df)
                elif metadata.get('error'):
                    st.error(f"❌ Error in {file_name}: {metadata['error']}")
            
            # Combined export for parallel results
            if len(all_results) > 1:
                combined_df = pd.concat(all_results, ignore_index=True)
                st.subheader("📦 Export All Results")
                self.export_manager.render_export_options(combined_df, "combined_search_results")
    
    def _display_file_results(self, result_df: pd.DataFrame, file_name: str, container):
        """Display results from a single file."""
        with container:
            st.subheader(f"📄 Results from: {file_name}")
            st.caption(f"Found {len(result_df):,} matches")
            
            # Pagination for large results
            if len(result_df) > config.search.default_page_size:
                page_size = st.selectbox(
                    f"Rows per page ({file_name}):",
                    [100, 500, 1000, 2000],
                    value=config.search.default_page_size,
                    key=f"page_size_{file_name}"
                )
                
                total_pages = (len(result_df) + page_size - 1) // page_size
                
                if total_pages > 1:
                    page = st.number_input(
                        f"Page ({file_name}):",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        key=f"page_{file_name}"
                    )
                    
                    start_idx = (page - 1) * page_size
                    end_idx = min(start_idx + page_size, len(result_df))
                    display_df = result_df.iloc[start_idx:end_idx]
                else:
                    display_df = result_df
            else:
                display_df = result_df
            
            # Display data
            st.dataframe(display_df, use_container_width=True)
            
            # Export options for this file
            self.export_manager.render_export_options(
                display_df, 
                f"{os.path.splitext(file_name)[0]}_results"
            )
            
            st.divider()

# Global search interface instance
search_interface = SearchInterface()