import yaml
import os
from pathlib import Path

def load_config():
    """Load configuration from config.yaml, fallback to config.yaml.example"""
    config_path = Path("config.yaml")
    example_path = Path("config.yaml.example")
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    elif example_path.exists():
        print("Warning: config.yaml not found, using config.yaml.example")
        with open(example_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        raise FileNotFoundError("Neither config.yaml nor config.yaml.example found")

def configure_duckdb(con, config=None):
    """Apply DuckDB configuration settings"""
    if config is None:
        config = load_config()
    
    duckdb_config = config.get('duckdb', {})
    
    if 'memory_limit' in duckdb_config:
        con.execute(f"SET memory_limit='{duckdb_config['memory_limit']}'")
    
    if 'max_memory' in duckdb_config:
        con.execute(f"SET max_memory='{duckdb_config['max_memory']}'")
    
    if 'threads' in duckdb_config:
        con.execute(f"SET threads={duckdb_config['threads']}")
    
    if 'temp_directory' in duckdb_config:
        con.execute(f"SET temp_directory='{duckdb_config['temp_directory']}'")

def get_directories(config=None):
    """Get directory paths from config"""
    if config is None:
        config = load_config()
    
    dirs = config.get('directories', {})
    return {
        'input_dir': dirs.get('input_dir', 'data/csv'),
        'output_dir': dirs.get('output_dir', 'data/parq'),
        'log_dir': dirs.get('log_dir', 'logs')
    }