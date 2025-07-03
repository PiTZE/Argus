"""File processing and CSV to DuckDB conversion."""

import os
import time
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.database.connection import db_manager
from src.core.config import config
from src.core.logging_config import perf_logger

logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles CSV file processing and conversion to DuckDB tables."""
    
    def __init__(self):
        self.con = db_manager.get_connection()
    
    def get_file_hash(self, file_path: str) -> str:
        """Generate a unique hash for the file path."""
        return hashlib.md5(file_path.encode()).hexdigest()[:8]
    
    def get_table_name(self, file_path: str) -> str:
        """Generate a unique table name for the file."""
        file_hash = self.get_file_hash(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        # Clean base name for SQL compatibility
        clean_name = ''.join(c if c.isalnum() else '_' for c in base_name)
        return f"csv_{clean_name}_{file_hash}"
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file metadata."""
        try:
            stat = os.stat(file_path)
            file_size_mb = stat.st_size / (1024 * 1024)
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            return {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size_mb': file_size_mb,
                'last_modified': last_modified,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {e}")
            return {'exists': False, 'error': str(e)}
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if file has been processed and is up to date."""
        try:
            metadata = self.get_file_metadata(file_path)
            if not metadata['exists']:
                return False
            
            # Check if metadata exists in database
            result = db_manager.execute_query(
                "SELECT last_modified, table_name FROM file_metadata WHERE file_path = ?",
                [file_path]
            )
            
            if result.empty:
                return False
            
            db_last_modified = pd.to_datetime(result.iloc[0]['last_modified'])
            file_last_modified = pd.to_datetime(metadata['last_modified'])
            
            # Check if table still exists
            table_name = result.iloc[0]['table_name']
            if not db_manager.table_exists(table_name):
                return False
            
            return db_last_modified >= file_last_modified
            
        except Exception as e:
            logger.error(f"Error checking if file is processed: {e}")
            return False
    
    def convert_csv_to_table(self, file_path: str, progress_callback=None) -> bool:
        """Convert CSV file to DuckDB table with optimizations for large files."""
        start_time = time.time()
        table_name = self.get_table_name(file_path)
        
        try:
            if progress_callback:
                progress_callback(f"Processing {os.path.basename(file_path)}...")
            
            # Get file metadata
            metadata = self.get_file_metadata(file_path)
            if not metadata['exists']:
                raise Exception(f"File does not exist: {file_path}")
            
            # Escape file path for SQL
            escaped_path = file_path.replace("'", "''")
            
            # Create table with optimizations for large files
            create_query = f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_csv_auto('{escaped_path}', 
                    HEADER=TRUE, 
                    IGNORE_ERRORS=TRUE,
                    SAMPLE_SIZE=100000,
                    AUTO_DETECT=TRUE,
                    NORMALIZE_NAMES=TRUE
                );
            """
            
            if progress_callback:
                progress_callback(f"Creating table for {os.path.basename(file_path)}...")
            
            self.con.execute(create_query)
            
            # Get table information
            table_info = db_manager.get_table_info(table_name)
            if not table_info['exists']:
                raise Exception("Failed to create table")
            
            row_count = table_info['row_count']
            columns = [col['name'] for col in table_info['columns']]
            column_types = [col['type'] for col in table_info['columns']]
            
            if progress_callback:
                progress_callback(f"Creating indexes for {os.path.basename(file_path)}...")
            
            # Create indexes on text/varchar columns for faster searching
            indexed_columns = []
            for col_info in table_info['columns']:
                col_name = col_info['name']
                col_type = col_info['type'].upper()
                
                if any(t in col_type for t in ['VARCHAR', 'TEXT', 'STRING']):
                    try:
                        index_name = f"idx_{table_name}_{col_name}"
                        self.con.execute(f'CREATE INDEX {index_name} ON {table_name}("{col_name}");')
                        indexed_columns.append(col_name)
                    except Exception as e:
                        logger.warning(f"Failed to create index on {col_name}: {e}")
            
            # Store metadata in database
            with db_manager.transaction():
                # Remove existing metadata
                db_manager.execute_query(
                    "DELETE FROM file_metadata WHERE file_path = ?",
                    [file_path],
                    fetch=False
                )
                
                # Insert new metadata
                db_manager.execute_query("""
                    INSERT INTO file_metadata 
                    (file_path, file_name, file_size_mb, row_count, column_names, 
                     column_types, last_modified, table_name, indexed_columns)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    file_path,
                    metadata['file_name'],
                    metadata['file_size_mb'],
                    row_count,
                    columns,
                    column_types,
                    metadata['last_modified'],
                    table_name,
                    indexed_columns
                ], fetch=False)
            
            duration = time.time() - start_time
            perf_logger.log_file_processing(file_path, "CSV_TO_TABLE", duration, True)
            
            logger.info(f"Successfully processed {file_path} -> {table_name} "
                       f"({row_count:,} rows, {len(indexed_columns)} indexes, {duration:.2f}s)")
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            perf_logger.log_file_processing(file_path, "CSV_TO_TABLE", duration, False)
            logger.error(f"Failed to process {file_path}: {e}")
            return False
    
    def process_files_parallel(self, file_paths: List[str], 
                             progress_callback=None) -> Dict[str, bool]:
        """Process multiple CSV files in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=config.search.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.convert_csv_to_table, file_path, progress_callback): file_path
                for file_path in file_paths
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    results[file_path] = success
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    results[file_path] = False
        
        return results
    
    def get_all_file_metadata(self) -> pd.DataFrame:
        """Get metadata for all processed files."""
        return db_manager.execute_query("""
            SELECT file_path, file_name, file_size_mb, row_count, 
                   column_names, last_modified, table_name, indexed_columns
            FROM file_metadata 
            ORDER BY file_name
        """)
    
    def get_column_distribution(self) -> Dict[str, List[str]]:
        """Get distribution of columns across all files."""
        metadata_df = self.get_all_file_metadata()
        column_to_files = {}
        
        for _, row in metadata_df.iterrows():
            file_path = row['file_path']
            columns = row['column_names']
            
            for column in columns:
                if column not in column_to_files:
                    column_to_files[column] = []
                column_to_files[column].append(file_path)
        
        return column_to_files
    
    def cleanup_orphaned_tables(self):
        """Remove tables for files that no longer exist."""
        try:
            metadata_df = self.get_all_file_metadata()
            removed_count = 0
            
            for _, row in metadata_df.iterrows():
                file_path = row['file_path']
                table_name = row['table_name']
                
                if not os.path.exists(file_path):
                    # Remove table
                    self.con.execute(f"DROP TABLE IF EXISTS {table_name};")
                    
                    # Remove metadata
                    db_manager.execute_query(
                        "DELETE FROM file_metadata WHERE file_path = ?",
                        [file_path],
                        fetch=False
                    )
                    
                    removed_count += 1
                    logger.info(f"Removed orphaned table: {table_name}")
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} orphaned tables")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global file processor instance
file_processor = FileProcessor()