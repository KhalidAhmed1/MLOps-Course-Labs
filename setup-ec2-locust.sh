#!/bin/bash
# EC2 Setup Script - Deploy and run Locust load tests on EC2

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
EC2_IP=${1:-}
API_PORT=${2:-8000}
TEST_TYPE=${3:-headless}

# Function to print usage
usage() {
    cat << EOF
${BLUE}EC2 Locust Setup Script${NC}

Usage: ./setup-ec2-locust.sh <EC2_IP> [API_PORT] [TEST_TYPE]

Arguments:
    EC2_IP          EC2 instance IP address (required)
    API_PORT        Port where API is running (default: 8000)
    TEST_TYPE       Type of test: web, headless (default: headless)

Examples:
    # Web UI mode
    ./setup-ec2-locust.sh 54.123.45.67 8000 web

    # Headless mode
    ./setup-ec2-locust.sh 54.123.45.67 8000 headless

${YELLOW}Prerequisites:${NC}
    1. EC2 instance must be running
    2. API must be deployed and running on the instance
    3. SSH key pair configured in ~/.ssh/
    4. Security group allows inbound on port 8000 (API) and 8089 (Locust UI)
EOF
}

if [ -z "$EC2_IP" ]; then
    echo -e "${RED}Error: EC2_IP is required${NC}"
    usage
    exit 1
fi

echo -e "${BLUE}=== EC2 Locust Setup ===${NC}\n"
echo -e "Target EC2 IP: ${GREEN}$EC2_IP${NC}"
echo -e "API Port: ${GREEN}$API_PORT${NC}"
echo -e "Test Type: ${GREEN}$TEST_TYPE${NC}\n"

# Step 1: Verify connectivity
echo -e "${YELLOW}Step 1: Verifying EC2 connectivity...${NC}"
if ping -c 1 "$EC2_IP" &> /dev/null; then
    echo -e "${GREEN}✓ EC2 instance is reachable${NC}\n"
else
    echo -e "${RED}✗ Cannot reach EC2 instance at $EC2_IP${NC}"
    echo "Please check:"
    echo "  1. EC2 instance is running"
    echo "  2. EC2 IP is correct"
    echo "  3. Security group allows ICMP"
    exit 1
fi

# Step 2: Check API health
echo -e "${YELLOW}Step 2: Checking API health...${NC}"
API_URL="http://$EC2_IP:$API_PORT"
if curl -sf "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is running and healthy${NC}\n"
else
    echo -e "${RED}✗ API is not responding at $API_URL${NC}"
    echo "Please ensure:"
    echo "  1. API is deployed and running on the EC2 instance"
    echo "  2. Port $API_PORT is correct"
    echo "  3. Security group allows inbound on port $API_PORT"
    exit 1
fi

# Step 3: Install Locust locally if not present
echo -e "${YELLOW}Step 3: Installing Locust...${NC}"
if command -v locust &> /dev/null; then
    echo -e "${GREEN}✓ Locust is already installed${NC}\n"
else
    echo -e "${YELLOW}Installing Locust via pip...${NC}"
    pip install locust
    echo -e "${GREEN}✓ Locust installed successfully${NC}\n"
fi

# Step 4: Run the load test
echo -e "${YELLOW}Step 4: Starting load test...${NC}"
echo -e "Test URL: ${GREEN}$API_URL${NC}"
echo ""

case $TEST_TYPE in
    web)
        echo -e "${BLUE}Running in Web UI mode${NC}"
        echo -e "Open your browser to: ${GREEN}http://localhost:8089${NC}"
        echo -e "Set host to: ${GREEN}$API_URL${NC}\n"
        locust -f locustfile.py --host="$API_URL"
        ;;
    headless)
        echo -e "${BLUE}Running in Headless mode (10 minutes test, 100 users)${NC}"
        echo ""
        locust -f locustfile.py \
            --host="$API_URL" \
            --users=100 \
            --spawn-rate=10 \
            --run-time=10m \
            --headless \
            --csv=results
        
        echo -e "\n${GREEN}Test completed!${NC}"
        if [ -f "results_stats.csv" ]; then
            echo -e "Results saved to: ${GREEN}results_stats.csv${NC}"
            echo -e "\nFirst 10 results:"
            head -n 10 results_stats.csv
        fi
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        usage
        exit 1
        ;;
esac

echo -e "\n${GREEN}=== Setup Complete ===${NC}"
