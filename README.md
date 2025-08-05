# Argus 👁👁

a simple web interface for tabular data.

## Setup
Clone the Repo:
```bash
git clone https://github.com/PiTZE/Argus.git && cd Argus
```

Then Install Using:
```bash
./manage.sh install
```
This creates a virtual environment, installs dependencies, and copies the config file. (Needs python and pip to work)

## Usage

### Start web interface
```bash
./manage.sh start
```
Access at http://localhost:8501 or http://your-server-ip:8501 
if port 8501 is taken by something else it choose 8502 and so on.

### Convert CSV files
Place CSV files in `data/csv/` directory first.
```bash
./manage.sh process-data
```

### Stop web interface
```bash
./manage.sh stop
```

### Service management
Install as systemd service:
```bash
./manage.sh service --install
```

System-wide service (requires sudo):
```bash
sudo ./manage.sh service --install --system
```

Service control:
```bash
./manage.sh service --start    # Start service
./manage.sh service --stop     # Stop service
./manage.sh service --status   # Check status
./manage.sh service --logs     # View logs
./manage.sh service --remove   # Uninstall service
```

### Help
```bash
./manage.sh help
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