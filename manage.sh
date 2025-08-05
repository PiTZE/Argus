#!/bin/bash

set -e

# ============================================================================
# VARIABLES AND CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PID_FILE="$SCRIPT_DIR/argus.pid"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
CONFIG_EXAMPLE="$SCRIPT_DIR/config.yaml.example"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
MAIN_SCRIPT="$SCRIPT_DIR/src/main.py"
CSV_PROCESSOR="$SCRIPT_DIR/src/csv_to_parq.py"

SERVICE_NAME="argus"
SERVICE_FILE_USER="$HOME/.config/systemd/user/$SERVICE_NAME.service"
SERVICE_FILE_SYSTEM="/etc/systemd/system/$SERVICE_NAME.service"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

check_venv() {
    # Check if virtual environment exists and exit if not found
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found"
        log_error "Run './manage.sh install' first"
        exit 1
    fi
}

activate_venv() {
    # Activate the virtual environment after checking it exists
    check_venv
    source "$VENV_DIR/bin/activate"
}

# ============================================================================
# APPLICATION MANAGEMENT
# ============================================================================

install_app() {
    # Setup virtual environment and dependencies
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
    # Start the Argus web interface
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
    # Stop the running Argus web interface
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
    # Convert CSV files to Parquet format
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

# ============================================================================
# SERVICE MANAGEMENT FUNCTIONS
# ============================================================================

create_service_file() {
    # Create systemd service file with provided configuration
    local service_file="$1"
    local service_type="$2"
    
    cat > "$service_file" << EOF
[Unit]
Description=Argus Streamlit Application
After=network.target
Wants=network.target

[Service]
Type=forking
User=$(whoami)
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/manage.sh start
ExecStop=$SCRIPT_DIR/manage.sh stop
PIDFile=$SCRIPT_DIR/argus.pid
Restart=always
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=60
Environment=PATH=$SCRIPT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF
}

install_service() {
    # Install and configure systemd service
    log_info "Installing Argus service..."
    
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl not found. This system doesn't support systemd services."
        exit 1
    fi
    
    local use_user_service=true
    local service_file="$SERVICE_FILE_USER"
    local systemctl_cmd="systemctl --user"
    
    if [[ "$1" == "--system" ]]; then
        if [[ $EUID -ne 0 ]]; then
            log_error "System service installation requires root privileges"
            log_info "Run with sudo or use user service (default)"
            exit 1
        fi
        use_user_service=false
        service_file="$SERVICE_FILE_SYSTEM"
        systemctl_cmd="systemctl"
    fi
    
    if [[ "$use_user_service" == true ]]; then
        mkdir -p "$(dirname "$SERVICE_FILE_USER")"
    fi
    
    if [[ -f "$service_file" ]]; then
        log_warning "Service file already exists: $service_file"
        log_info "Use 'service --remove' first to reinstall"
        exit 1
    fi
    
    log_info "Creating service file: $service_file"
    create_service_file "$service_file" "$use_user_service"
    
    log_info "Reloading systemd daemon..."
    $systemctl_cmd daemon-reload
    
    log_info "Enabling service..."
    $systemctl_cmd enable "$SERVICE_NAME"
    
    log_info "Starting service..."
    $systemctl_cmd start "$SERVICE_NAME"
    
    sleep 2
    if $systemctl_cmd is-active --quiet "$SERVICE_NAME"; then
        log_success "Service installed and started successfully"
        if [[ "$use_user_service" == true ]]; then
            log_info "Service type: User service"
            log_info "Control with: systemctl --user {start|stop|status|restart} $SERVICE_NAME"
        else
            log_info "Service type: System service"
            log_info "Control with: systemctl {start|stop|status|restart} $SERVICE_NAME"
        fi
    else
        log_error "Service installation failed"
        $systemctl_cmd status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

remove_service() {
    # Remove and cleanup systemd service
    log_info "Removing Argus service..."
    
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl not found. This system doesn't support systemd services."
        exit 1
    fi
    
    local service_file=""
    local systemctl_cmd=""
    local service_exists=false
    
    if [[ -f "$SERVICE_FILE_USER" ]]; then
        service_file="$SERVICE_FILE_USER"
        systemctl_cmd="systemctl --user"
        service_exists=true
        log_info "Found user service"
    elif [[ -f "$SERVICE_FILE_SYSTEM" ]]; then
        if [[ $EUID -ne 0 ]]; then
            log_error "System service removal requires root privileges"
            exit 1
        fi
        service_file="$SERVICE_FILE_SYSTEM"
        systemctl_cmd="systemctl"
        service_exists=true
        log_info "Found system service"
    fi
    
    if [[ "$service_exists" == false ]]; then
        log_warning "No service installation found"
        exit 0
    fi
    
    log_info "Stopping service..."
    $systemctl_cmd stop "$SERVICE_NAME" 2>/dev/null || true
    
    log_info "Disabling service..."
    $systemctl_cmd disable "$SERVICE_NAME" 2>/dev/null || true
    
    log_info "Removing service file: $service_file"
    rm -f "$service_file"
    
    log_info "Reloading systemd daemon..."
    $systemctl_cmd daemon-reload
    
    log_success "Service removed successfully"
}

start_service() {
    # Start the systemd service
    log_info "Starting Argus service..."
    
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl not found. This system doesn't support systemd services."
        exit 1
    fi
    
    local systemctl_cmd=""
    
    if [[ -f "$SERVICE_FILE_USER" ]]; then
        systemctl_cmd="systemctl --user"
    elif [[ -f "$SERVICE_FILE_SYSTEM" ]]; then
        systemctl_cmd="systemctl"
    else
        log_error "No service installation found"
        log_info "Run 'service --install' first"
        exit 1
    fi
    
    $systemctl_cmd enable "$SERVICE_NAME"
    $systemctl_cmd start "$SERVICE_NAME"
    
    sleep 2
    if $systemctl_cmd is-active --quiet "$SERVICE_NAME"; then
        log_success "Service started successfully"
    else
        log_error "Failed to start service"
        $systemctl_cmd status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

stop_service() {
    # Stop the systemd service
    log_info "Stopping Argus service..."
    
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl not found. This system doesn't support systemd services."
        exit 1
    fi
    
    local systemctl_cmd=""
    
    if [[ -f "$SERVICE_FILE_USER" ]]; then
        systemctl_cmd="systemctl --user"
    elif [[ -f "$SERVICE_FILE_SYSTEM" ]]; then
        systemctl_cmd="systemctl"
    else
        log_error "No service installation found"
        exit 1
    fi
    
    $systemctl_cmd stop "$SERVICE_NAME"
    $systemctl_cmd disable "$SERVICE_NAME"
    
    log_success "Service stopped and disabled"
}

status_service() {
    # Show systemd service status
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl not found. This system doesn't support systemd services."
        exit 1
    fi
    
    local systemctl_cmd=""
    
    if [[ -f "$SERVICE_FILE_USER" ]]; then
        systemctl_cmd="systemctl --user"
        log_info "Service type: User service"
    elif [[ -f "$SERVICE_FILE_SYSTEM" ]]; then
        systemctl_cmd="systemctl"
        log_info "Service type: System service"
    else
        log_error "No service installation found"
        exit 1
    fi
    
    $systemctl_cmd status "$SERVICE_NAME" --no-pager
}

logs_service() {
    # Display systemd service logs
    if ! command -v journalctl &> /dev/null; then
        log_error "journalctl not found. Cannot view service logs."
        exit 1
    fi
    
    local journalctl_cmd=""
    
    if [[ -f "$SERVICE_FILE_USER" ]]; then
        journalctl_cmd="journalctl --user"
    elif [[ -f "$SERVICE_FILE_SYSTEM" ]]; then
        journalctl_cmd="journalctl"
    else
        log_error "No service installation found"
        exit 1
    fi
    
    log_info "Showing service logs (press Ctrl+C to exit)..."
    $journalctl_cmd -u "$SERVICE_NAME" -f
}

show_help() {
    # Display usage information and available commands
    echo "Usage: $0 [install|start|stop|process-data|service|help]"
    echo ""
    echo "Commands:"
    echo "  install             Setup virtual environment and dependencies"
    echo "  start               Start web interface"
    echo "  stop                Stop web interface"
    echo "  process-data        Convert CSV files to Parquet"
    echo "  service             Manage systemd service"
    echo "  help                Show this help"
    echo ""
    echo "Service Commands:"
    echo "  service --install   Install, enable and start systemd service"
    echo "  service --remove    Stop, disable and remove systemd service"
    echo "  service --start     Start and enable systemd service"
    echo "  service --stop      Stop and disable systemd service"
    echo "  service --status    Show service status"
    echo "  service --logs      Show service logs (follow mode)"
    echo ""
    echo "Service Options:"
    echo "  --system            Install as system service (requires sudo)"
    echo "                      Default: user service"
    echo ""
    echo "Examples:"
    echo "  $0 service --install                # Install user service"
    echo "  sudo $0 service --install --system  # Install system service"
    echo "  $0 service --status                 # Check service status"
    echo ""
    echo "Note: Run 'install' first before using other commands"
}

# ============================================================================
# MAIN SCRIPT LOGIC
# ============================================================================

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
    service)
        case "${2:-}" in
            --install)
                install_service "$3"
                ;;
            --remove)
                remove_service
                ;;
            --start)
                start_service
                ;;
            --stop)
                stop_service
                ;;
            --status)
                status_service
                ;;
            --logs)
                logs_service
                ;;
            *)
                log_error "Unknown service command: $2"
                echo ""
                echo "Available service commands:"
                echo "  --install   Install, enable and start service"
                echo "  --remove    Stop, disable and remove service"
                echo "  --start     Start and enable service"
                echo "  --stop      Stop and disable service"
                echo "  --status    Show service status"
                echo "  --logs      Show service logs"
                exit 1
                ;;
        esac
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