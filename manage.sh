#!/bin/bash
# ZyraX Bot Management Script
# Helper script to start, stop, and manage the bot

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if bot is running
is_bot_running() {
    pgrep -f "python.*bot.py" > /dev/null 2>&1
}

# Function to check PM2 status
is_pm2_running() {
    pm2 list 2>/dev/null | grep -q "zyrax.*online"
}

# Start bot directly (not with PM2)
start_direct() {
    print_info "Starting ZyraX bot directly..."
    
    if is_bot_running; then
        print_warning "Bot is already running!"
        ps aux | grep "python.*bot.py" | grep -v grep
        return 1
    fi
    
    # Activate virtual environment and run
    source venv/bin/activate
    python3.12 bot.py
}

# Start bot with PM2
start_pm2() {
    print_info "Starting ZyraX bot with PM2..."
    
    if is_pm2_running; then
        print_warning "Bot is already running in PM2!"
        pm2 list
        return 1
    fi
    
    # Check if ecosystem config exists
    if [ ! -f "ecosystem.config.js" ]; then
        print_error "ecosystem.config.js not found!"
        if [ -f "ecosystem.config.example.js" ]; then
            print_info "Creating ecosystem.config.js from example..."
            cp ecosystem.config.example.js ecosystem.config.js
        else
            print_error "Please create ecosystem.config.js first"
            return 1
        fi
    fi
    
    pm2 start ecosystem.config.js
    print_success "Bot started with PM2"
    pm2 list
}

# Stop bot
stop_bot() {
    print_info "Stopping ZyraX bot..."
    
    # Stop PM2 instance if running
    if is_pm2_running; then
        print_info "Stopping PM2 instance..."
        pm2 stop zyrax
        pm2 delete zyrax
        print_success "PM2 instance stopped"
    fi
    
    # Kill any remaining Python processes
    if is_bot_running; then
        print_info "Killing remaining bot processes..."
        pkill -f "python.*bot.py" || true
        sleep 2
        
        # Force kill if still running
        if is_bot_running; then
            print_warning "Force killing bot processes..."
            pkill -9 -f "python.*bot.py" || true
        fi
    fi
    
    # Clean up session locks
    if [ -f "data/sessions/zyrax_bot.session-journal" ]; then
        print_info "Cleaning up session journal..."
        rm -f data/sessions/zyrax_bot.session-journal
    fi
    
    print_success "Bot stopped"
}

# Restart bot
restart_bot() {
    print_info "Restarting ZyraX bot..."
    stop_bot
    sleep 2
    
    if [ "$1" = "pm2" ]; then
        start_pm2
    else
        start_direct
    fi
}

# Show bot status
show_status() {
    print_info "ZyraX Bot Status"
    echo "===================="
    
    # Check direct processes
    if is_bot_running; then
        print_success "Bot process is running:"
        ps aux | grep "python.*bot.py" | grep -v grep
    else
        print_warning "No direct bot processes found"
    fi
    
    echo ""
    
    # Check PM2
    if command -v pm2 &> /dev/null; then
        print_info "PM2 Status:"
        pm2 list 2>/dev/null || print_warning "PM2 not running"
    fi
    
    echo ""
    
    # Check session files
    print_info "Session files:"
    ls -lh data/sessions/ 2>/dev/null || print_warning "No session directory found"
}

# Clean session locks
clean_locks() {
    print_info "Cleaning session locks..."
    
    if is_bot_running; then
        print_error "Please stop the bot first: $0 stop"
        return 1
    fi
    
    rm -f data/sessions/zyrax_bot.session-journal
    print_success "Session locks cleaned"
}

# Show logs
show_logs() {
    if [ -f "data/logs/bot.log" ]; then
        tail -f data/logs/bot.log
    else
        print_error "Log file not found: data/logs/bot.log"
    fi
}

# Show help
show_help() {
    cat << EOF
ZyraX Bot Management Script

Usage: $0 <command> [options]

Commands:
    start           Start bot directly (foreground)
    start-pm2       Start bot with PM2 (background)
    stop            Stop bot (PM2 and direct processes)
    restart         Restart bot directly
    restart-pm2     Restart bot with PM2
    status          Show bot status
    logs            Show real-time logs
    clean-locks     Clean session lock files (stop bot first)
    help            Show this help message

Examples:
    $0 start         # Start bot in foreground
    $0 start-pm2     # Start bot with PM2
    $0 stop          # Stop all bot instances
    $0 logs          # View logs in real-time
    $0 status        # Check if bot is running

EOF
}

# Main script logic
case "$1" in
    start)
        start_direct
        ;;
    start-pm2)
        start_pm2
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    restart-pm2)
        restart_bot pm2
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    clean-locks)
        clean_locks
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
