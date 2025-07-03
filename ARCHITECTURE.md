# 🏗️ Architecture Overview

## Project Structure

```
csv-search-app/
├── src/                          # Source code modules
│   ├── core/                     # Core configuration and logging
│   │   ├── config.py            # Configuration management
│   │   └── logging_config.py    # Logging setup
│   ├── database/                # Database layer
│   │   ├── connection.py        # DuckDB connection management
│   │   ├── file_processor.py    # CSV to DuckDB conversion
│   │   └── search_engine.py     # High-performance search engine
│   ├── auth/                    # Authentication
│   │   └── auth_manager.py      # User authentication
│   ├── ui/                      # User interface components
│   │   ├── dashboard.py         # Data overview dashboard
│   │   ├── search_interface.py  # Search interface
│   │   ├── file_manager.py      # File upload/management
│   │   └── export_utils.py      # Export functionality
│   └── utils/                   # Utility functions
│       └── helpers.py           # Common helper functions
├── main.py                      # Main application entry point
├── config.yaml                  # Configuration file
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
└── db/                         # CSV files directory
```

## Key Components

### 🗄️ **Database Layer**
- **DuckDB**: High-performance analytical database
- **Persistent Storage**: CSV files converted to optimized tables
- **Indexing**: Automatic indexes on searchable columns
- **Memory Management**: 8GB+ memory limits with external sorting

### 🔍 **Search Engine**
- **Parallel Processing**: Multi-threaded file processing
- **Streaming Results**: Handle large result sets without memory issues
- **Query Caching**: Cache frequent searches for instant results
- **Smart Pagination**: Efficient handling of millions of results

### 🎨 **User Interface**
- **Modular Design**: Separate components for different features
- **Responsive Layout**: Works on desktop and mobile
- **Real-time Progress**: Live progress bars for long operations
- **Interactive Charts**: Plotly-based data visualizations

### 🔐 **Security**
- **Authentication**: bcrypt password hashing
- **Session Management**: Secure cookie-based sessions
- **Input Validation**: SQL injection protection
- **Audit Logging**: Track user actions and performance

## Performance Optimizations

### 🚀 **For Large Files (2GB+)**

1. **Persistent Database Storage**
   - Convert CSV files to DuckDB tables once
   - Query optimized columnar storage instead of raw CSV
   - 10-50x faster searches after initial conversion

2. **Memory Management**
   - Configurable memory limits (default 8GB)
   - External sorting for data larger than memory
   - Streaming results to prevent memory overflow

3. **Parallel Processing**
   - Multi-threaded file processing
   - Concurrent searches across multiple files
   - Background CSV conversion

4. **Smart Caching**
   - Query result caching
   - Metadata caching with TTL
   - File modification detection

5. **Chunked Processing**
   - Stream results in configurable chunks
   - Progressive display of results
   - Pagination for large result sets

## Data Flow

```
CSV Files → File Processor → DuckDB Tables → Search Engine → UI Components
    ↓              ↓              ↓              ↓              ↓
Upload/Scan → Convert/Index → Store/Cache → Query/Stream → Display/Export
```

### 📊 **Search Process**
1. **File Discovery**: Scan for CSV files in db/ directory
2. **Metadata Extraction**: Analyze file structure and columns
3. **Table Conversion**: Convert CSV to optimized DuckDB tables
4. **Index Creation**: Create indexes on text/varchar columns
5. **Query Execution**: Execute SQL queries with parameters
6. **Result Streaming**: Stream results in chunks to UI
7. **Export Options**: Provide CSV, Excel, JSON export

## Configuration

### 🔧 **Database Settings**
```yaml
database:
  memory_limit: "8GB"        # Memory limit for DuckDB
  threads: 4                 # Number of processing threads
  external_sorting: true     # Enable external sorting
  db_path: "data/search_app.duckdb"  # Database file location
```

### 🔍 **Search Settings**
```yaml
search:
  default_chunk_size: 1000   # Results per chunk
  max_result_limit: 50000    # Maximum results per file
  max_workers: 3             # Parallel processing workers
  cache_ttl_seconds: 3600    # Cache expiration time
```

### 🎨 **UI Settings**
```yaml
ui:
  max_upload_size_mb: 2048   # Maximum file upload size
  page_title: "Gharp Search - Large CSV Analytics"
  layout: "wide"             # Streamlit layout mode
```

## Scalability Considerations

### 📈 **Horizontal Scaling**
- **Multiple Workers**: Increase `max_workers` for more parallel processing
- **Memory Scaling**: Increase `memory_limit` based on available RAM
- **Storage Scaling**: Use fast SSD storage for database files

### 🔄 **Performance Monitoring**
- **Execution Time Logging**: Track search performance
- **Memory Usage Monitoring**: Monitor system resources
- **Cache Hit Rates**: Track caching effectiveness
- **Error Rate Monitoring**: Monitor system health

### 🛠️ **Maintenance**
- **Automatic Cleanup**: Remove orphaned tables
- **Index Optimization**: Rebuild indexes periodically
- **Cache Management**: Automatic cache expiration
- **Log Rotation**: Automatic log file rotation

## Security Architecture

### 🔐 **Authentication Flow**
1. User submits credentials
2. bcrypt password verification
3. JWT token generation
4. Secure cookie storage
5. Session validation on requests

### 🛡️ **Data Protection**
- **SQL Injection Prevention**: Parameterized queries
- **Input Sanitization**: Clean user inputs
- **File Access Control**: Restricted file operations
- **Audit Trail**: Log all user actions

## Deployment Options

### 🐳 **Docker Deployment**
```bash
docker build -t gharp-search .
docker run -p 12000:12000 -v ./data:/app/data gharp-search
```

### ☁️ **Cloud Deployment**
- **Memory Requirements**: 8GB+ RAM recommended
- **Storage Requirements**: Fast SSD for database files
- **Network**: HTTPS recommended for production
- **Monitoring**: Health checks and logging

## Future Enhancements

### 🚀 **Planned Features**
- **API Endpoints**: REST API for programmatic access
- **Real-time Collaboration**: Multi-user search sessions
- **Advanced Analytics**: Statistical analysis and aggregations
- **Data Visualization**: Interactive charts and dashboards
- **Scheduled Searches**: Automated recurring searches
- **Data Lineage**: Track data sources and transformations