"""Advanced search engine for large CSV files."""

import time
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple, Generator
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.database.connection import db_manager
from src.database.file_processor import file_processor
from src.core.config import config
from src.core.logging_config import perf_logger

logger = logging.getLogger(__name__)

class SearchEngine:
    """High-performance search engine for large CSV files."""
    
    def __init__(self):
        self.con = db_manager.get_connection()
    
    def build_search_query(self, search_term: str, search_type: str, 
                          column_name: str, table_name: str, 
                          limit: int = None) -> Tuple[str, List[str]]:
        """Build optimized SQL query based on search type."""
        
        # Escape column name
        escaped_column = f'"{column_name}"'
        
        # Build WHERE clause based on search type
        if search_type == "Exact match":
            where_clause = f"{escaped_column}::VARCHAR = ?"
            params = [search_term]
        elif search_type == "Starts with":
            where_clause = f"{escaped_column}::VARCHAR ILIKE ?"
            params = [f"{search_term}%"]
        elif search_type == "Ends with":
            where_clause = f"{escaped_column}::VARCHAR ILIKE ?"
            params = [f"%{search_term}"]
        elif search_type == "Regex":
            where_clause = f"regexp_matches({escaped_column}::VARCHAR, ?)"
            params = [search_term]
        else:  # Contains (case-insensitive) - default
            where_clause = f"{escaped_column}::VARCHAR ILIKE ?"
            params = [f"%{search_term}%"]
        
        # Build complete query
        query = f"""
            SELECT * FROM {table_name}
            WHERE {where_clause}
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        return query, params
    
    def get_search_cache_key(self, search_term: str, search_type: str, 
                           column_name: str, file_paths: List[str]) -> str:
        """Generate cache key for search results."""
        content = f"{search_term}|{search_type}|{column_name}|{'|'.join(sorted(file_paths))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_results(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search results if available and not expired."""
        try:
            result = db_manager.execute_query("""
                SELECT result_count, execution_time_ms, created_at
                FROM search_cache 
                WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
            """, [cache_key])
            
            if not result.empty:
                return result.iloc[0].to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached results: {e}")
            return None
    
    def cache_search_results(self, cache_key: str, result_count: int, 
                           execution_time_ms: int):
        """Cache search results for future use."""
        try:
            # Calculate expiration time
            expires_at = pd.Timestamp.now() + pd.Timedelta(seconds=config.search.cache_ttl_seconds)
            
            # Store in cache
            db_manager.execute_query("""
                INSERT OR REPLACE INTO search_cache 
                (cache_key, query_hash, result_count, execution_time_ms, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, [cache_key, cache_key, result_count, execution_time_ms, expires_at], fetch=False)
            
        except Exception as e:
            logger.error(f"Error caching search results: {e}")
    
    def search_single_file(self, file_path: str, search_term: str, 
                          search_type: str, column_name: str, 
                          limit: int = None) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """Search a single file and return results with metadata."""
        start_time = time.time()
        
        try:
            # Get table name from metadata
            metadata_result = db_manager.execute_query(
                "SELECT table_name FROM file_metadata WHERE file_path = ?",
                [file_path]
            )
            
            if metadata_result.empty:
                return None, {'error': 'File not processed', 'duration': 0}
            
            table_name = metadata_result.iloc[0]['table_name']
            
            # Check if table exists
            if not db_manager.table_exists(table_name):
                return None, {'error': 'Table not found', 'duration': 0}
            
            # Build and execute query
            query, params = self.build_search_query(
                search_term, search_type, column_name, table_name, limit
            )
            
            results_df = db_manager.execute_query(query, params)
            
            duration = time.time() - start_time
            
            return results_df, {
                'success': True,
                'duration': duration,
                'row_count': len(results_df),
                'table_name': table_name
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error searching file {file_path}: {e}")
            return None, {'error': str(e), 'duration': duration}
    
    def stream_search_results(self, file_path: str, search_term: str, 
                            search_type: str, column_name: str,
                            chunk_size: int = None) -> Generator[pd.DataFrame, None, Dict[str, Any]]:
        """Stream search results in chunks for large result sets."""
        
        if chunk_size is None:
            chunk_size = config.search.default_chunk_size
        
        start_time = time.time()
        total_rows = 0
        
        try:
            # Get table name
            metadata_result = db_manager.execute_query(
                "SELECT table_name FROM file_metadata WHERE file_path = ?",
                [file_path]
            )
            
            if metadata_result.empty:
                return {'error': 'File not processed', 'duration': 0, 'total_rows': 0}
            
            table_name = metadata_result.iloc[0]['table_name']
            
            # Get total count first
            count_query, params = self.build_search_query(
                search_term, search_type, column_name, table_name
            )
            count_query = f"SELECT COUNT(*) as total FROM ({count_query}) as subq"
            
            total_count_result = db_manager.execute_query(count_query, params)
            total_count = total_count_result.iloc[0]['total']
            
            if total_count == 0:
                return {'success': True, 'duration': time.time() - start_time, 'total_rows': 0}
            
            # Stream results in chunks
            offset = 0
            while offset < total_count:
                query, params = self.build_search_query(
                    search_term, search_type, column_name, table_name
                )
                query += f" LIMIT {chunk_size} OFFSET {offset}"
                
                chunk_df = db_manager.execute_query(query, params)
                
                if chunk_df.empty:
                    break
                
                total_rows += len(chunk_df)
                yield chunk_df
                
                offset += chunk_size
            
            duration = time.time() - start_time
            return {
                'success': True,
                'duration': duration,
                'total_rows': total_rows,
                'total_count': total_count
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error streaming results from {file_path}: {e}")
            return {'error': str(e), 'duration': duration, 'total_rows': total_rows}
    
    def search_multiple_files(self, file_paths: List[str], search_term: str,
                            search_type: str, column_name: str,
                            limit_per_file: int = None) -> Dict[str, Any]:
        """Search multiple files in parallel."""
        
        start_time = time.time()
        results = {}
        total_results = 0
        successful_searches = 0
        
        # Check cache first
        cache_key = self.get_search_cache_key(search_term, search_type, column_name, file_paths)
        cached = self.get_cached_results(cache_key)
        
        if cached:
            logger.info(f"Using cached results for search: {search_term}")
            return {
                'cached': True,
                'cache_info': cached,
                'total_files': len(file_paths)
            }
        
        # Execute parallel search
        with ThreadPoolExecutor(max_workers=config.search.max_workers) as executor:
            # Submit search tasks
            future_to_file = {
                executor.submit(
                    self.search_single_file, 
                    file_path, search_term, search_type, column_name, limit_per_file
                ): file_path
                for file_path in file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                file_name = os.path.basename(file_path)
                
                try:
                    result_df, metadata = future.result()
                    
                    if result_df is not None and not result_df.empty:
                        results[file_path] = {
                            'data': result_df,
                            'metadata': metadata,
                            'file_name': file_name
                        }
                        total_results += len(result_df)
                        successful_searches += 1
                    else:
                        results[file_path] = {
                            'data': None,
                            'metadata': metadata,
                            'file_name': file_name
                        }
                        
                except Exception as e:
                    logger.error(f"Error processing search result for {file_path}: {e}")
                    results[file_path] = {
                        'data': None,
                        'metadata': {'error': str(e), 'duration': 0},
                        'file_name': file_name
                    }
        
        total_duration = time.time() - start_time
        
        # Cache results
        self.cache_search_results(cache_key, total_results, int(total_duration * 1000))
        
        return {
            'results': results,
            'total_results': total_results,
            'successful_searches': successful_searches,
            'total_files': len(file_paths),
            'total_duration': total_duration,
            'cached': False
        }
    
    def save_search_history(self, user_name: str, search_term: str, 
                          column_name: str, search_type: str,
                          files_searched: int, results_found: int, 
                          execution_time_ms: int):
        """Save search to history."""
        try:
            db_manager.execute_query("""
                INSERT INTO search_history 
                (user_name, search_term, column_name, search_type, 
                 files_searched, results_found, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                user_name, search_term, column_name, search_type,
                files_searched, results_found, execution_time_ms
            ], fetch=False)
            
        except Exception as e:
            logger.error(f"Error saving search history: {e}")
    
    def get_search_history(self, user_name: str, limit: int = 10) -> pd.DataFrame:
        """Get recent search history for user."""
        return db_manager.execute_query("""
            SELECT search_term, column_name, search_type, files_searched,
                   results_found, execution_time_ms, created_at
            FROM search_history 
            WHERE user_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, [user_name, limit])
    
    def get_popular_searches(self, limit: int = 5) -> pd.DataFrame:
        """Get most popular search terms."""
        return db_manager.execute_query("""
            SELECT search_term, column_name, COUNT(*) as search_count,
                   AVG(execution_time_ms) as avg_time_ms,
                   SUM(results_found) as total_results
            FROM search_history 
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY search_term, column_name
            ORDER BY search_count DESC
            LIMIT ?
        """, [limit])

# Global search engine instance
search_engine = SearchEngine()