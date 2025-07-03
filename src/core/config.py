"""Configuration management for the CSV Search App."""

import os
import yaml
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    memory_limit: str = "8GB"
    threads: int = 4
    temp_directory: str = "/tmp/duckdb_temp"
    external_sorting: bool = True
    preserve_insertion_order: bool = False
    db_path: str = "data/search_app.duckdb"

@dataclass
class SearchConfig:
    """Search configuration settings."""
    default_chunk_size: int = 1000
    max_result_limit: int = 50000
    default_page_size: int = 500
    max_workers: int = 3
    large_file_threshold_mb: float = 100.0
    cache_ttl_seconds: int = 3600

@dataclass
class UIConfig:
    """UI configuration settings."""
    page_title: str = "Gharp Search - Large CSV Analytics"
    layout: str = "wide"
    max_upload_size_mb: int = 2048
    progress_update_interval: int = 5

@dataclass
class SecurityConfig:
    """Security configuration settings."""
    session_timeout_hours: int = 8
    max_login_attempts: int = 5
    password_min_length: int = 8
    require_strong_passwords: bool = True

class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.database = DatabaseConfig()
        self.search = SearchConfig()
        self.ui = UIConfig()
        self.security = SecurityConfig()
        self._auth_config = None
        
        self.load_config()
        self.ensure_directories()
    
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as file:
                    config_data = yaml.safe_load(file)
                    
                # Load auth config
                self._auth_config = config_data
                
                # Load other configs if they exist
                if 'database' in config_data:
                    db_config = config_data['database']
                    for key, value in db_config.items():
                        if hasattr(self.database, key):
                            setattr(self.database, key, value)
                
                if 'search' in config_data:
                    search_config = config_data['search']
                    for key, value in search_config.items():
                        if hasattr(self.search, key):
                            setattr(self.search, key, value)
                            
                if 'ui' in config_data:
                    ui_config = config_data['ui']
                    for key, value in ui_config.items():
                        if hasattr(self.ui, key):
                            setattr(self.ui, key, value)
                            
                if 'security' in config_data:
                    security_config = config_data['security']
                    for key, value in security_config.items():
                        if hasattr(self.security, key):
                            setattr(self.security, key, value)
                            
        except Exception as e:
            logger.warning(f"Could not load config from {self.config_path}: {e}")
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            os.path.dirname(self.database.db_path),
            self.database.temp_directory,
            "db",
            "logs",
            "exports"
        ]
        
        for directory in directories:
            if directory:
                os.makedirs(directory, exist_ok=True)
    
    @property
    def auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration."""
        return self._auth_config or {}
    
    def get_env_var(self, key: str, default: Any = None) -> Any:
        """Get environment variable with fallback to default."""
        return os.getenv(key, default)

# Global config instance
config = Config()