# Argus

a simple web interface for tabular data.

## Setup

```bash
./manage.sh install
```

This creates a virtual environment, installs dependencies, and copies the config file.

## Usage

### Start web interface
```bash
./manage.sh start
```
Access at http://localhost:8501

### Convert CSV files
```bash
./manage.sh process-data
```
Place CSV files in `data/csv/` directory first.

### Stop web interface
```bash
./manage.sh stop
```

## Configuration

Edit `config.yaml` to change:
- Memory limits (default: 256MB)
- Directory paths
- CSV parsing options
- Log levels

## Data Processing

The converter:
- Processes files by size (smallest first)
- Applies type conversion based on column names
- Compresses output with GZIP
- Logs to `logs/` directory
- Skips existing output files

## Web Interface

Features:
- File and column selection
- Text search across data
- Results displayed in table format