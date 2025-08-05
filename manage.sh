#!/bin/bash

set -e

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PID_FILE="$SCRIPT_DIR/argus.pid"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
CONFIG_EXAMPLE="$SCRIPT_DIR/config.yaml.example"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
MAIN_SCRIPT="$SCRIPT_DIR/src/main.py"
CSV_PROCESSOR="$SCRIPT_DIR/src/csv_to_parq.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Helper functions
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found"
        log_error "Run './manage.sh install' first"
        exit 1
    fi
}

activate_venv() {
    check_venv
    source "$VENV_DIR/bin/activate"
}

install_app() {
    log_info "Installing Argus..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    source "$VENV_DIR/bin/activate"
    
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    if [ -f "$REQUIREMENTS_FILE" ]; then
        log_info "Installing dependencies..."
        pip install -r "$REQUIREMENTS_FILE"
    else
        log_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    if [ -f "$CONFIG_EXAMPLE" ]; then
        if [ ! -f "$CONFIG_FILE" ]; then
            log_info "Creating config.yaml..."
            cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"
            log_warning "Review and modify $CONFIG_FILE as needed"
        else
            log_warning "config.yaml already exists, skipping"
        fi
    else
        log_error "Configuration example not found: $CONFIG_EXAMPLE"
        exit 1
    fi
    
    mkdir -p data/csv data/parq logs
    log_success "Installation complete"
}

start_app() {
    log_info "Starting Argus..."
    
    activate_venv
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_warning "Already running (PID: $PID)"
            exit 0
        else
            log_warning "Stale PID file found, removing..."
            rm -f "$PID_FILE"
        fi
    fi
    
    if [ ! -f "$MAIN_SCRIPT" ]; then
        log_error "Main script not found: $MAIN_SCRIPT"
        exit 1
    fi
    
    mkdir -p logs
    cd "$SCRIPT_DIR"
    
    log_info "Launching Streamlit..."
    nohup streamlit run "$MAIN_SCRIPT" > logs/argus.log 2>&1 &
    
    echo $! > "$PID_FILE"
    log_success "Started (PID: $(cat $PID_FILE))"
    sleep 3
    if [ -f "logs/argus.log" ]; then
        LOCAL_URL=$(grep -o "Local URL: http://[^[:space:]]*" logs/argus.log | tail -1 | cut -d' ' -f3)
        NETWORK_URL=$(grep -o "Network URL: http://[^[:space:]]*" logs/argus.log | tail -1 | cut -d' ' -f3)
        
        if [ -n "$LOCAL_URL" ]; then
            log_info "$LOCAL_URL"
        else
            log_info "Local URL: http://localhost:8501"
        fi
        
        if [ -n "$NETWORK_URL" ]; then
            log_info "$NETWORK_URL"
        fi
    else
        log_info "Local URL: http://localhost:8501"
    fi
}

stop_app() {
    log_info "Stopping Argus..."
    
    if [ ! -f "$PID_FILE" ]; then
        log_warning "Not running"
        exit 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if kill -0 "$PID" 2>/dev/null; then
        log_info "Stopping process (PID: $PID)"
        kill "$PID"
        
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        if kill -0 "$PID" 2>/dev/null; then
            log_warning "Force killing process..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        log_success "Stopped"
    else
        log_warning "Process not running"
        rm -f "$PID_FILE"
    fi
}

process_data() {
    log_info "Processing CSV data..."
    
    activate_venv
    
    if [ ! -f "$CSV_PROCESSOR" ]; then
        log_error "CSV processor not found: $CSV_PROCESSOR"
        exit 1
    fi
    
    cd "$SCRIPT_DIR"
    python "$CSV_PROCESSOR"
    
    if [ $? -eq 0 ]; then
        log_success "Data processing complete"
    else
        log_error "Data processing failed"
        exit 1
    fi
}

show_help() {
    echo "Usage: $0 [install|start|stop|process-data|help]"
    echo ""
    echo "Commands:"
    echo "  install             Setup virtual environment and dependencies"
    echo "  start               Start web interface"
    echo "  stop                Stop web interface"
    echo "  process-data        Convert CSV files to Parquet"
    echo "  help                Show this help"
    echo ""
    echo "Note: Run 'install' first before using other commands"
}

# Main script logic
case "${1:-help}" in
    install)
        install_app
        ;;
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    process-data)
        process_data
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac