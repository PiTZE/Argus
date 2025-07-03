"""File management and upload interface."""

import streamlit as st
import os
import shutil
import logging
from typing import List, Dict, Any
import pandas as pd
from src.database.file_processor import file_processor
from src.core.config import config

logger = logging.getLogger(__name__)

class FileManager:
    """Manages file uploads and CSV file processing."""
    
    def __init__(self):
        self.upload_dir = "db"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def render_file_upload_interface(self):
        """Render file upload interface."""
        st.header("📁 File Management")
        
        # File upload section
        with st.expander("📤 Upload CSV Files", expanded=True):
            uploaded_files = st.file_uploader(
                "Choose CSV files",
                type=['csv'],
                accept_multiple_files=True,
                help=f"Upload CSV files (max {config.ui.max_upload_size_mb}MB each)"
            )
            
            if uploaded_files:
                self._process_uploaded_files(uploaded_files)
        
        # Existing files section
        self._render_existing_files()
        
        # File processing section
        self._render_file_processing()
    
    def _process_uploaded_files(self, uploaded_files):
        """Process and save uploaded files."""
        st.subheader("📥 Processing Uploads")
        
        upload_results = []
        
        for uploaded_file in uploaded_files:
            try:
                # Check file size
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                
                if file_size_mb > config.ui.max_upload_size_mb:
                    st.error(f"❌ {uploaded_file.name}: File too large ({file_size_mb:.1f}MB). "
                            f"Maximum allowed: {config.ui.max_upload_size_mb}MB")
                    continue
                
                # Save file
                file_path = os.path.join(self.upload_dir, uploaded_file.name)
                
                # Check if file already exists
                if os.path.exists(file_path):
                    overwrite = st.checkbox(
                        f"Overwrite existing {uploaded_file.name}?",
                        key=f"overwrite_{uploaded_file.name}"
                    )
                    if not overwrite:
                        st.warning(f"⚠️ Skipped {uploaded_file.name} (already exists)")
                        continue
                
                # Save the file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Validate CSV format
                try:
                    sample_df = pd.read_csv(file_path, nrows=5)
                    upload_results.append({
                        'name': uploaded_file.name,
                        'size_mb': file_size_mb,
                        'columns': len(sample_df.columns),
                        'status': 'success',
                        'path': file_path
                    })
                    st.success(f"✅ {uploaded_file.name} uploaded successfully "
                              f"({file_size_mb:.1f}MB, {len(sample_df.columns)} columns)")
                    
                except Exception as e:
                    os.remove(file_path)  # Remove invalid file
                    st.error(f"❌ {uploaded_file.name}: Invalid CSV format - {e}")
                    upload_results.append({
                        'name': uploaded_file.name,
                        'status': 'error',
                        'error': str(e)
                    })
                    
            except Exception as e:
                logger.error(f"Error processing upload {uploaded_file.name}: {e}")
                st.error(f"❌ {uploaded_file.name}: Upload failed - {e}")
        
        # Process uploaded files automatically
        if upload_results:
            successful_uploads = [r for r in upload_results if r['status'] == 'success']
            if successful_uploads:
                if st.button("🔄 Process Uploaded Files", type="primary"):
                    self._process_files_for_search([r['path'] for r in successful_uploads])
    
    def _render_existing_files(self):
        """Render existing files in the database directory."""
        csv_files = [f for f in os.listdir(self.upload_dir) if f.endswith('.csv')]
        
        if not csv_files:
            st.info("📂 No CSV files found. Upload files to get started.")
            return
        
        with st.expander(f"📂 Existing Files ({len(csv_files)})", expanded=False):
            # Get processed file metadata
            try:
                metadata_df = file_processor.get_all_file_metadata()
                processed_files = set(metadata_df['file_path'].tolist()) if not metadata_df.empty else set()
            except:
                processed_files = set()
            
            for csv_file in sorted(csv_files):
                file_path = os.path.join(self.upload_dir, csv_file)
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    # File status
                    if file_path in processed_files:
                        st.write(f"✅ **{csv_file}** ({file_size_mb:.1f}MB) - *Processed*")
                    else:
                        st.write(f"⏳ **{csv_file}** ({file_size_mb:.1f}MB) - *Not processed*")
                
                with col2:
                    # Preview button
                    if st.button("👀", key=f"preview_{csv_file}", help="Preview file"):
                        self._show_file_preview(file_path)
                
                with col3:
                    # Process button
                    if file_path not in processed_files:
                        if st.button("🔄", key=f"process_{csv_file}", help="Process file"):
                            self._process_files_for_search([file_path])
                
                with col4:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{csv_file}", help="Delete file"):
                        if st.session_state.get(f"confirm_delete_{csv_file}"):
                            self._delete_file(file_path)
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{csv_file}"] = True
                            st.warning(f"Click again to confirm deletion of {csv_file}")
    
    def _render_file_processing(self):
        """Render file processing controls."""
        with st.expander("⚙️ File Processing", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Process All Unprocessed Files", type="secondary"):
                    self._process_all_unprocessed_files()
                
                if st.button("🧹 Cleanup Orphaned Tables", help="Remove tables for deleted files"):
                    self._cleanup_orphaned_tables()
            
            with col2:
                if st.button("🔄 Reprocess All Files", help="Reprocess all files (updates indexes)"):
                    self._reprocess_all_files()
                
                if st.button("📊 Refresh Metadata", help="Refresh file metadata cache"):
                    st.cache_data.clear()
                    st.success("✅ Metadata cache cleared")
    
    def _show_file_preview(self, file_path: str):
        """Show preview of CSV file."""
        try:
            df = pd.read_csv(file_path, nrows=10)
            
            st.subheader(f"👀 Preview: {os.path.basename(file_path)}")
            st.write(f"**Columns:** {', '.join(df.columns.tolist())}")
            st.write(f"**Sample data (first 10 rows):**")
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error previewing file: {e}")
    
    def _process_files_for_search(self, file_paths: List[str]):
        """Process files for search functionality."""
        if not file_paths:
            return
        
        st.subheader("🔄 Processing Files for Search")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success_count = 0
        
        for i, file_path in enumerate(file_paths):
            file_name = os.path.basename(file_path)
            status_text.info(f"Processing {file_name}...")
            
            try:
                success = file_processor.convert_csv_to_table(
                    file_path,
                    lambda msg: status_text.info(msg)
                )
                
                if success:
                    success_count += 1
                    status_text.success(f"✅ {file_name} processed successfully")
                else:
                    status_text.error(f"❌ Failed to process {file_name}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                status_text.error(f"❌ Error processing {file_name}: {e}")
            
            progress_bar.progress((i + 1) / len(file_paths))
        
        progress_bar.empty()
        status_text.success(
            f"🎉 Processing complete! {success_count}/{len(file_paths)} files processed successfully."
        )
        
        # Clear cache to refresh metadata
        st.cache_data.clear()
    
    def _process_all_unprocessed_files(self):
        """Process all unprocessed CSV files."""
        csv_files = [
            os.path.join(self.upload_dir, f) 
            for f in os.listdir(self.upload_dir) 
            if f.endswith('.csv')
        ]
        
        if not csv_files:
            st.info("No CSV files found to process")
            return
        
        # Filter unprocessed files
        try:
            metadata_df = file_processor.get_all_file_metadata()
            processed_files = set(metadata_df['file_path'].tolist()) if not metadata_df.empty else set()
        except:
            processed_files = set()
        
        unprocessed_files = [f for f in csv_files if f not in processed_files]
        
        if not unprocessed_files:
            st.info("All files are already processed")
            return
        
        self._process_files_for_search(unprocessed_files)
    
    def _reprocess_all_files(self):
        """Reprocess all CSV files."""
        csv_files = [
            os.path.join(self.upload_dir, f) 
            for f in os.listdir(self.upload_dir) 
            if f.endswith('.csv')
        ]
        
        if not csv_files:
            st.info("No CSV files found to process")
            return
        
        if st.button("⚠️ Confirm Reprocess All", type="secondary"):
            self._process_files_for_search(csv_files)
    
    def _cleanup_orphaned_tables(self):
        """Clean up orphaned database tables."""
        try:
            file_processor.cleanup_orphaned_tables()
            st.success("✅ Orphaned tables cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            st.error(f"❌ Cleanup failed: {e}")
    
    def _delete_file(self, file_path: str):
        """Delete a CSV file and its associated data."""
        try:
            file_name = os.path.basename(file_path)
            
            # Remove from database if processed
            try:
                metadata_df = file_processor.get_all_file_metadata()
                if not metadata_df.empty:
                    file_metadata = metadata_df[metadata_df['file_path'] == file_path]
                    if not file_metadata.empty:
                        table_name = file_metadata.iloc[0]['table_name']
                        
                        # Drop table and metadata
                        con = file_processor.con
                        con.execute(f"DROP TABLE IF EXISTS {table_name};")
                        con.execute("DELETE FROM file_metadata WHERE file_path = ?", [file_path])
                        
            except Exception as e:
                logger.warning(f"Error removing database data for {file_path}: {e}")
            
            # Remove file
            os.remove(file_path)
            st.success(f"✅ {file_name} deleted successfully")
            
            # Clear cache
            st.cache_data.clear()
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            st.error(f"❌ Error deleting file: {e}")

# Global file manager instance
file_manager = FileManager()