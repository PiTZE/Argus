# Argus

A simple tool for converting CSV files to Parquet format and viewing the data through a web interface.

## Components

- **csv_to_parq.py** - Converts CSV files to compressed Parquet format
- **main.py** - Streamlit web app for searching and viewing the converted data
- **config.py** - Shared configuration utilities

## Setup

1. Clone the repository:
```bash
git clone https://github.com/PiTZE/Argus.git && cd Argus
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create configuration file:
```bash
cp config.yaml.example config.yaml
```

3. Adjust settings in `config.yaml` for your environment (memory limits, paths, etc.)

## Usage

### Convert CSV to Parquet

Place CSV files in `data/csv/` directory, then run:

```bash
python csv_to_parq.py
```

The script will:
- Process files in order of size (smallest first)
- Apply type conversion based on column names
- Compress output using GZIP
- Log progress and errors to `logs/` directory
- Skip files that already exist in output

### View Data

Start the web interface:

```bash
streamlit run main.py
```

Open http://localhost:8501 to:
- Select files and columns to search
- Run text searches across data
- View results in a table

## Configuration

Edit `config.yaml` to customize:

- **Memory limits** - DuckDB memory usage (default: 256MB)
- **Directories** - Input/output/log paths
- **CSV parsing** - Error handling, strict mode, etc.
- **Logging** - Console/file log levels