#!/bin/bash
# Startup Verification Script for Linux/Mac
# Run this after docker-compose up to verify all services are working

echo "========================================"
echo "  Fraud Detection System - Health Check"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    echo -n "Checking $name..."
    
    if curl -s -f -o /dev/null "$url"; then
        echo -e " ${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e " ${RED}✗ NOT ACCESSIBLE${NC}"
        return 1
    fi
}

# Function to check Docker container
check_container() {
    local name=$1
    echo -n "Checking container $name..."
    
    if docker ps --filter "name=$name" --format "{{.Status}}" | grep -q "Up"; then
        echo -e " ${GREEN}✓ RUNNING${NC}"
        return 0
    else
        echo -e " ${RED}✗ NOT RUNNING${NC}"
        return 1
    fi
}

echo -e "${YELLOW}1. Docker Containers Status${NC}"
echo "----------------------------"

containers=(
    "zookeeper"
    "kafka"
    "namenode"
    "datanode"
    "resourcemanager"
    "nodemanager"
    "postgres"
    "producer"
    "consumer"
    "backend"
    "frontend"
)

all_running=true
for container in "${containers[@]}"; do
    if ! check_container "$container"; then
        all_running=false
    fi
done

echo ""
echo -e "${YELLOW}2. Service Endpoints${NC}"
echo "--------------------"

all_healthy=true
check_endpoint "HDFS NameNode" "http://localhost:9870" || all_healthy=false
check_endpoint "YARN ResourceManager" "http://localhost:8088" || all_healthy=false
check_endpoint "Backend API" "http://localhost:8000/health" || all_healthy=false
check_endpoint "Frontend Dashboard" "http://localhost:8501" || all_healthy=false

echo ""
echo -e "${YELLOW}3. Data Verification${NC}"
echo "--------------------"

# Check HDFS data
echo -n "Checking HDFS data..."
if docker exec namenode hadoop fs -ls /data/raw/transactions/ &>/dev/null; then
    echo -e " ${GREEN}✓ HDFS accessible${NC}"
else
    echo -e " ${YELLOW}⚠ HDFS accessible but no data yet${NC}"
fi

# Check PostgreSQL
echo -n "Checking PostgreSQL..."
if docker exec postgres psql -U fraud_user -d frauddb -c "SELECT 1" &>/dev/null; then
    echo -e " ${GREEN}✓ Database accessible${NC}"
else
    echo -e " ${RED}✗ Database check failed${NC}"
fi

echo ""
echo "========================================"

if [ "$all_running" = true ] && [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✓ All systems operational!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Wait 2-3 minutes for data generation"
    echo "2. Open dashboard: http://localhost:8501"
    echo "3. Run pipeline: curl -X POST 'http://localhost:8000/pipeline/run?dt=2025-12-18'"
else
    echo -e "${YELLOW}⚠ Some services are not ready${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "- Wait 2-3 minutes for services to initialize"
    echo "- Check logs: docker-compose logs -f"
    echo "- Restart: docker-compose restart [service-name]"
fi

echo "========================================"
echo ""
