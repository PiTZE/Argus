#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PID_FILE="$SCRIPT_DIR/argus.pid"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
CONFIG_EXAMPLE="$SCRIPT_DIR/config.yaml.example"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
MAIN_SCRIPT="$SCRIPT_DIR/src/main.py"
CSV_PROCESSOR="$SCRIPT_DIR/src/csv_to_parq.py"

check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Error: Virtual environment not found"
        echo "Run './manage.sh install' first"
        exit 1
    fi
}

activate_venv() {
    check_venv
    source "$VENV_DIR/bin/activate"
}

install_app() {
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    source "$VENV_DIR/bin/activate"
    
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Creating config.yaml..."
        cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"
    fi
    
    mkdir -p data/csv data/parq logs
    echo "Installation complete"
}

start_app() {
    activate_venv
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Already running (PID: $PID)"
            exit 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    mkdir -p logs
    cd "$SCRIPT_DIR"
    nohup streamlit run "$MAIN_SCRIPT" --server.port 8501 --server.address 0.0.0.0 > logs/argus.log 2>&1 &
    
    echo $! > "$PID_FILE"
    echo "Started (PID: $(cat $PID_FILE))"
    echo "Access: http://localhost:8501"
}

stop_app() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Not running"
        exit 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "Stopped"
    else
        rm -f "$PID_FILE"
        echo "Not running"
    fi
}

process_data() {
    activate_venv
    cd "$SCRIPT_DIR"
    python "$CSV_PROCESSOR"
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
}

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
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac