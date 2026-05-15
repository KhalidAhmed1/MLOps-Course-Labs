#!/bin/bash
# Load testing helper script for Locust

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    cat << EOF
${BLUE}Load Testing Helper - Locust CLI Wrapper${NC}

Usage: ./run-load-test.sh [COMMAND] [OPTIONS]

Commands:
    web         Run Locust with web UI
    headless    Run Locust in headless mode
    distributed Run distributed load testing (master)
    worker      Run as worker node
    help        Show this help message

Options for 'web' and 'headless':
    --host=URL          API endpoint (default: http://localhost:8000)
    --users=NUM         Number of users (default: 10)
    --spawn-rate=NUM    Users per second (default: 1)
    --run-time=TIME     Test duration, e.g., 5m, 30s (headless only)

Examples:
    # Web UI against local API
    ./run-load-test.sh web

    # Headless against EC2
    ./run-load-test.sh headless --host=http://54.123.45.67:8000 --users=100 --spawn-rate=10 --run-time=5m

    # Distributed master
    ./run-load-test.sh distributed --host=http://54.123.45.67:8000

    # Worker node
    ./run-load-test.sh worker --master-host=master-ip
EOF
}

# Default values
COMMAND=${1:-web}
HOST="http://localhost:8000"
USERS=10
SPAWN_RATE=1
RUN_TIME="5m"
MASTER_HOST="localhost"
MASTER_PORT=5557

# Parse additional arguments
shift || true
for arg in "$@"; do
    case $arg in
        --host=*)
            HOST="${arg#*=}"
            ;;
        --users=*)
            USERS="${arg#*=}"
            ;;
        --spawn-rate=*)
            SPAWN_RATE="${arg#*=}"
            ;;
        --run-time=*)
            RUN_TIME="${arg#*=}"
            ;;
        --master-host=*)
            MASTER_HOST="${arg#*=}"
            ;;
        --master-port=*)
            MASTER_PORT="${arg#*=}"
            ;;
        *)
            echo "Unknown option: $arg"
            usage
            exit 1
            ;;
    esac
done

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${YELLOW}Locust not found. Installing...${NC}"
    pip install locust
fi

# Execute command
case $COMMAND in
    web)
        echo -e "${GREEN}Starting Locust Web UI...${NC}"
        echo -e "Host: ${BLUE}$HOST${NC}"
        echo -e "Open browser to: ${BLUE}http://localhost:8089${NC}"
        locust -f locustfile.py --host="$HOST"
        ;;
    headless)
        echo -e "${GREEN}Starting Locust Headless...${NC}"
        echo -e "Host: ${BLUE}$HOST${NC}"
        echo -e "Users: ${BLUE}$USERS${NC}"
        echo -e "Spawn Rate: ${BLUE}$SPAWN_RATE${NC}"
        echo -e "Duration: ${BLUE}$RUN_TIME${NC}"
        locust -f locustfile.py \
            --host="$HOST" \
            --users="$USERS" \
            --spawn-rate="$SPAWN_RATE" \
            --run-time="$RUN_TIME" \
            --headless
        ;;
    distributed)
        echo -e "${GREEN}Starting Locust Master (Distributed Mode)...${NC}"
        echo -e "Host: ${BLUE}$HOST${NC}"
        locust -f locustfile.py \
            --host="$HOST" \
            --master \
            --web \
            --expect-workers=2
        ;;
    worker)
        echo -e "${GREEN}Starting Locust Worker...${NC}"
        echo -e "Master Host: ${BLUE}$MASTER_HOST${NC}"
        echo -e "Master Port: ${BLUE}$MASTER_PORT${NC}"
        locust -f locustfile.py \
            --worker \
            --master-host="$MASTER_HOST" \
            --master-port="$MASTER_PORT"
        ;;
    help)
        usage
        ;;
    *)
        echo "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
