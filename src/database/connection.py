"""Database connection and management for DuckDB."""

import duckdb
import os
import logging
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from src.core.config import config
from src.core.logging_config import perf_logger

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages DuckDB connections and database operations."""
    
    def __init__(self):
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._initialized = False
    
    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection
    
    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create optimized DuckDB connection for large files."""
        try:
            # Ensure database directory exists
            os.makedirs(os.path.dirname(config.database.db_path), exist_ok=True)
            
            # Create connection
            con = duckdb.connect(config.database.db_path, read_only=False)
            
            # Configure for large file processing
            con.execute(f"SET memory_limit = '{config.database.memory_limit}';")
            con.execute(f"SET threads = {config.database.threads};")
            con.execute(f"SET temp_directory = '{config.database.temp_directory}';")
            con.execute(f"SET external_sorting = {config.database.external_sorting};")
            con.execute(f"SET preserve_insertion_order = {config.database.preserve_insertion_order};")
            
            # Install and load extensions
            con.execute("INSTALL icu;")
            con.execute("LOAD icu;")
            
            # Additional optimizations for large files
            con.execute("SET enable_progress_bar = false;")
            con.execute("SET enable_object_cache = true;")
            con.execute("SET max_memory = '8GB';")
            
            logger.info(f"Database connection established: {config.database.db_path}")
            return con
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            raise
    
    def initialize_schema(self):
        """Initialize database schema for metadata and caching."""
        if self._initialized:
            return
            
        con = self.get_connection()
        
        try:
            # File metadata table
            con.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    file_path VARCHAR PRIMARY KEY,
                    file_name VARCHAR NOT NULL,
                    file_size_mb DOUBLE NOT NULL,
                    row_count BIGINT NOT NULL,
                    column_names VARCHAR[] NOT NULL,
                    column_types VARCHAR[] NOT NULL,
                    last_modified TIMESTAMP NOT NULL,
                    table_name VARCHAR NOT NULL,
                    indexed_columns VARCHAR[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Search cache table
            con.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    cache_key VARCHAR PRIMARY KEY,
                    query_hash VARCHAR NOT NULL,
                    result_count BIGINT NOT NULL,
                    execution_time_ms BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                );
            """)
            
            # Search history table
            con.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY,
                    user_name VARCHAR NOT NULL,
                    search_term VARCHAR NOT NULL,
                    column_name VARCHAR NOT NULL,
                    search_type VARCHAR NOT NULL,
                    files_searched INTEGER NOT NULL,
                    results_found BIGINT NOT NULL,
                    execution_time_ms BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            self._initialized = True
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        con = self.get_connection()
        try:
            con.execute("BEGIN TRANSACTION;")
            yield con
            con.execute("COMMIT;")
        except Exception as e:
            con.execute("ROLLBACK;")
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    def execute_query(self, query: str, params: list = None, fetch: bool = True):
        """Execute query with performance logging."""
        start_time = time.time()
        con = self.get_connection()
        
        try:
            if params:
                result = con.execute(query, params)
            else:
                result = con.execute(query)
            
            duration = time.time() - start_time
            
            if fetch:
                data = result.fetchdf()
                perf_logger.log_database_operation(
                    "SELECT", "query", duration, len(data) if hasattr(data, '__len__') else 0
                )
                return data
            else:
                perf_logger.log_database_operation("EXECUTE", "query", duration)
                return result
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Query failed after {duration:.2f}s: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database."""
        try:
            con = self.get_connection()
            result = con.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table_name]
            ).fetchone()
            return result[0] > 0
        except Exception:
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table."""
        con = self.get_connection()
        
        try:
            # Get column information
            columns_info = con.execute(f"PRAGMA table_info('{table_name}');").fetchdf()
            
            # Get row count
            row_count = con.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0]
            
            return {
                'columns': columns_info.to_dict('records'),
                'row_count': row_count,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return {'exists': False, 'error': str(e)}
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()