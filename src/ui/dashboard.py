"""Dashboard and data overview components."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import os
import logging
from src.database.file_processor import file_processor
from src.database.search_engine import search_engine
from src.core.config import config

logger = logging.getLogger(__name__)

class Dashboard:
    """Main dashboard for data overview and analytics."""
    
    def __init__(self):
        pass
    
    def show_overview_metrics(self):
        """Display overview metrics cards."""
        try:
            metadata_df = file_processor.get_all_file_metadata()
            
            if metadata_df.empty:
                st.info("📁 No CSV files processed yet. Upload files to get started.")
                return
            
            # Calculate metrics
            total_files = len(metadata_df)
            total_rows = metadata_df['row_count'].sum()
            total_size_mb = metadata_df['file_size_mb'].sum()
            
            # Get unique columns
            all_columns = set()
            for columns_list in metadata_df['column_names']:
                all_columns.update(columns_list)
            unique_columns = len(all_columns)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📁 Total Files", 
                    f"{total_files:,}",
                    help="Number of CSV files processed"
                )
            
            with col2:
                st.metric(
                    "📊 Total Rows", 
                    f"{total_rows:,}",
                    help="Total number of data rows across all files"
                )
            
            with col3:
                st.metric(
                    "💾 Total Size", 
                    f"{total_size_mb:.1f} MB",
                    help="Combined size of all processed files"
                )
            
            with col4:
                st.metric(
                    "🏷️ Unique Columns", 
                    f"{unique_columns:,}",
                    help="Number of unique column names across all files"
                )
            
        except Exception as e:
            logger.error(f"Error displaying overview metrics: {e}")
            st.error(f"❌ Error loading overview: {e}")
    
    def show_file_details(self):
        """Display detailed file information."""
        try:
            metadata_df = file_processor.get_all_file_metadata()
            
            if metadata_df.empty:
                return
            
            with st.expander("📋 File Details", expanded=False):
                # File size distribution chart
                if len(metadata_df) > 1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # File size chart
                        fig_size = px.bar(
                            metadata_df,
                            x='file_name',
                            y='file_size_mb',
                            title='File Sizes (MB)',
                            labels={'file_size_mb': 'Size (MB)', 'file_name': 'File'}
                        )
                        fig_size.update_xaxis(tickangle=45)
                        st.plotly_chart(fig_size, use_container_width=True)
                    
                    with col2:
                        # Row count chart
                        fig_rows = px.bar(
                            metadata_df,
                            x='file_name',
                            y='row_count',
                            title='Row Counts',
                            labels={'row_count': 'Rows', 'file_name': 'File'}
                        )
                        fig_rows.update_xaxis(tickangle=45)
                        st.plotly_chart(fig_rows, use_container_width=True)
                
                # Detailed table
                st.subheader("📊 File Statistics")
                
                # Prepare display dataframe
                display_df = metadata_df.copy()
                display_df['file_size_mb'] = display_df['file_size_mb'].round(2)
                display_df['row_count'] = display_df['row_count'].apply(lambda x: f"{x:,}")
                display_df['column_count'] = display_df['column_names'].apply(len)
                display_df['indexed_columns_count'] = display_df['indexed_columns'].apply(
                    lambda x: len(x) if x else 0
                )
                
                # Select columns for display
                display_columns = [
                    'file_name', 'file_size_mb', 'row_count', 
                    'column_count', 'indexed_columns_count', 'last_modified'
                ]
                
                st.dataframe(
                    display_df[display_columns],
                    column_config={
                        'file_name': 'File Name',
                        'file_size_mb': 'Size (MB)',
                        'row_count': 'Rows',
                        'column_count': 'Columns',
                        'indexed_columns_count': 'Indexed Columns',
                        'last_modified': 'Last Modified'
                    },
                    use_container_width=True
                )
                
        except Exception as e:
            logger.error(f"Error displaying file details: {e}")
            st.error(f"❌ Error loading file details: {e}")
    
    def show_column_analysis(self):
        """Display column distribution analysis."""
        try:
            column_distribution = file_processor.get_column_distribution()
            
            if not column_distribution:
                return
            
            with st.expander("🏷️ Column Analysis", expanded=False):
                # Column frequency chart
                column_freq = {col: len(files) for col, files in column_distribution.items()}
                freq_df = pd.DataFrame(list(column_freq.items()), columns=['Column', 'File Count'])
                freq_df = freq_df.sort_values('File Count', ascending=False)
                
                if len(freq_df) > 0:
                    fig = px.bar(
                        freq_df.head(20),  # Show top 20 columns
                        x='File Count',
                        y='Column',
                        orientation='h',
                        title='Column Distribution (Top 20)',
                        labels={'File Count': 'Number of Files', 'Column': 'Column Name'}
                    )
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Column details table
                st.subheader("📋 Column Details")
                
                # Create detailed column info
                column_details = []
                for column, files in column_distribution.items():
                    column_details.append({
                        'Column Name': column,
                        'File Count': len(files),
                        'Files': ', '.join([os.path.basename(f) for f in files[:3]]) + 
                                ('...' if len(files) > 3 else '')
                    })
                
                column_df = pd.DataFrame(column_details)
                column_df = column_df.sort_values('File Count', ascending=False)
                
                st.dataframe(column_df, use_container_width=True)
                
        except Exception as e:
            logger.error(f"Error displaying column analysis: {e}")
            st.error(f"❌ Error loading column analysis: {e}")
    
    def show_search_analytics(self, user_name: str):
        """Display search analytics and history."""
        try:
            # Recent searches
            recent_searches = search_engine.get_search_history(user_name, limit=10)
            
            if not recent_searches.empty:
                with st.expander("🔍 Recent Searches", expanded=False):
                    # Format the dataframe for display
                    display_searches = recent_searches.copy()
                    display_searches['execution_time_ms'] = display_searches['execution_time_ms'].apply(
                        lambda x: f"{x/1000:.2f}s"
                    )
                    display_searches['results_found'] = display_searches['results_found'].apply(
                        lambda x: f"{x:,}"
                    )
                    
                    st.dataframe(
                        display_searches,
                        column_config={
                            'search_term': 'Search Term',
                            'column_name': 'Column',
                            'search_type': 'Type',
                            'files_searched': 'Files',
                            'results_found': 'Results',
                            'execution_time_ms': 'Duration',
                            'created_at': 'When'
                        },
                        use_container_width=True
                    )
            
            # Popular searches (global)
            popular_searches = search_engine.get_popular_searches(limit=5)
            
            if not popular_searches.empty:
                with st.expander("🔥 Popular Searches (Last 7 Days)", expanded=False):
                    display_popular = popular_searches.copy()
                    display_popular['avg_time_ms'] = display_popular['avg_time_ms'].apply(
                        lambda x: f"{x/1000:.2f}s"
                    )
                    display_popular['total_results'] = display_popular['total_results'].apply(
                        lambda x: f"{x:,}"
                    )
                    
                    st.dataframe(
                        display_popular,
                        column_config={
                            'search_term': 'Search Term',
                            'column_name': 'Column',
                            'search_count': 'Times Searched',
                            'avg_time_ms': 'Avg Duration',
                            'total_results': 'Total Results'
                        },
                        use_container_width=True
                    )
                    
        except Exception as e:
            logger.error(f"Error displaying search analytics: {e}")
            st.error(f"❌ Error loading search analytics: {e}")
    
    def show_performance_insights(self):
        """Display performance insights and recommendations."""
        try:
            metadata_df = file_processor.get_all_file_metadata()
            
            if metadata_df.empty:
                return
            
            with st.expander("⚡ Performance Insights", expanded=False):
                # Large files warning
                large_files = metadata_df[
                    metadata_df['file_size_mb'] > config.search.large_file_threshold_mb
                ]
                
                if not large_files.empty:
                    st.warning(
                        f"⚠️ **{len(large_files)} large files detected** "
                        f"(>{config.search.large_file_threshold_mb}MB). "
                        f"Consider using smaller result limits for better performance."
                    )
                    
                    for _, file_info in large_files.iterrows():
                        st.write(
                            f"• **{file_info['file_name']}**: "
                            f"{file_info['file_size_mb']:.1f} MB, "
                            f"{file_info['row_count']:,} rows"
                        )
                
                # Indexing status
                total_text_columns = 0
                indexed_columns = 0
                
                for _, file_info in metadata_df.iterrows():
                    # Count text columns (simplified check)
                    text_cols = len([col for col in file_info['column_names'] 
                                   if any(keyword in col.lower() 
                                         for keyword in ['name', 'text', 'description', 'title'])])
                    total_text_columns += text_cols
                    indexed_columns += len(file_info['indexed_columns'] or [])
                
                if total_text_columns > 0:
                    index_ratio = indexed_columns / max(total_text_columns, 1)
                    if index_ratio < 0.5:
                        st.info(
                            f"💡 **Indexing Opportunity**: Only {indexed_columns} of "
                            f"{total_text_columns} text columns are indexed. "
                            f"Re-processing files may improve search performance."
                        )
                
                # Memory usage recommendations
                total_size_gb = metadata_df['file_size_mb'].sum() / 1024
                if total_size_gb > 4:
                    st.info(
                        f"💾 **Memory Recommendation**: Total data size is {total_size_gb:.1f}GB. "
                        f"Consider increasing memory limit in configuration for optimal performance."
                    )
                    
        except Exception as e:
            logger.error(f"Error displaying performance insights: {e}")
            st.error(f"❌ Error loading performance insights: {e}")
    
    def render_full_dashboard(self, user_name: str):
        """Render the complete dashboard."""
        st.header("📊 Data Overview Dashboard")
        
        # Overview metrics
        self.show_overview_metrics()
        
        # File details and analysis
        col1, col2 = st.columns(2)
        
        with col1:
            self.show_file_details()
            self.show_performance_insights()
        
        with col2:
            self.show_column_analysis()
            self.show_search_analytics(user_name)

# Global dashboard instance
dashboard = Dashboard()