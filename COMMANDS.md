#  Command Cheat Sheet - Fraud Detection System

## System Status Commands

```powershell
# Check all services
docker-compose ps

# View combined logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f producer        # See transaction generation
docker-compose logs -f consumer        # See HDFS writes
docker-compose logs -f backend         # See API activity
```

## HDFS Commands

```powershell
# List data in HDFS
docker exec namenode hadoop fs -ls /data/raw/transactions/dt=2025-12-18/

# Count total files
docker exec namenode hadoop fs -find /data -type f | wc -l

# Check data size
docker exec namenode hadoop fs -du -h /data/

# Sample a transaction
docker exec namenode hadoop fs -cat "/data/raw/transactions/dt=2025-12-18/hour=14/part-*.jsonl" | Select-Object -First 1

# List all hourly partitions
docker exec namenode hadoop fs -ls /data/raw/transactions/dt=2025-12-18/ | findstr "hour"
```

## Pipeline Execution

```powershell
# Method 1: Via API (curl equivalent in PowerShell)
$response = Invoke-WebRequest -Uri "http://localhost:8000/pipeline/run?dt=2025-12-18" -Method Post
$response.Content | ConvertFrom-Json

# Method 2: Manual execution in backend container
docker exec backend bash /app/scripts/run_pipeline.sh 2025-12-18

# Method 3: Via Streamlit dashboard
# Open http://localhost:8501 -> Pipeline Control -> Run Pipeline
```

## Database Commands

```powershell
# Connect to PostgreSQL
docker exec -it postgres psql -U fraud_user -d frauddb

# In psql, useful queries:
\dt                           # List tables
SELECT COUNT(*) FROM merchant_daily_metrics;  # Row counts
SELECT COUNT(*) FROM alerts;
SELECT * FROM merchant_daily_metrics LIMIT 5;
SELECT rule_code, COUNT(*) FROM alerts GROUP BY rule_code;
\q                            # Exit psql
```

## API Testing

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8000/health" | Select-Object -ExpandProperty Content

# Get top merchants
Invoke-WebRequest -Uri "http://localhost:8000/metrics/merchants/top?dt=2025-12-18&metric=tx_count&n=5" | ConvertFrom-Json

# Get alerts
Invoke-WebRequest -Uri "http://localhost:8000/alerts?dt=2025-12-18&severity_min=2" | ConvertFrom-Json

# Get summary stats
Invoke-WebRequest -Uri "http://localhost:8000/stats/summary?dt=2025-12-18" | ConvertFrom-Json

# Visit Swagger UI for all endpoints
# Open browser to: http://localhost:8000/docs
```

## Service Management

```powershell
# Stop all services (keep volumes)
docker-compose stop

# Stop and remove everything
docker-compose down

# Full clean restart
docker-compose down -v --remove-orphans
docker-compose up -d

# Restart a specific service
docker-compose restart backend

# View service details
docker inspect namenode
```

## Monitoring

```powershell
# Watch Kafka messages in topic
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic transactions --from-beginning | Select-Object -First 10

# Check Kafka topic config
docker exec kafka kafka-topics --describe --bootstrap-server localhost:9092 --topic transactions

# Monitor CPU/Memory
docker stats

# Check container logs with timestamps
docker logs -f --timestamps backend
```

## Debug Commands

```powershell
# Enter container shell
docker exec -it namenode bash
docker exec -it backend bash
docker exec -it postgres psql -U fraud_user -d frauddb

# Check network connectivity
docker exec backend ping -c 5 postgres
docker exec producer ping -c 5 kafka

# View environment variables in container
docker exec backend env | Select-String "HDFS|POSTGRES|KAFKA"
```

## Data Verification Checklist

```powershell
# 1. Producer running?
docker logs producer --tail 3

# 2. Consumer writing to HDFS?
docker logs consumer --tail 3

# 3. Data in HDFS?
docker exec namenode hadoop fs -count /data/raw/transactions/

# 4. Database tables exist?
docker exec postgres psql -U fraud_user -d frauddb -c "\dt"

# 5. Backend API responding?
Invoke-WebRequest -Uri "http://localhost:8000/health"

# 6. Frontend dashboard accessible?
# Open http://localhost:8501 in browser
```

## Quick Demo Script

```powershell
# 1. Check system status
echo "=== SYSTEM STATUS ==="
docker-compose ps

# 2. Check data in HDFS
echo "=== DATA IN HDFS ==="
docker exec namenode hadoop fs -du -h /data/

# 3. Sample a transaction
echo "=== SAMPLE TRANSACTION ==="
docker exec namenode hadoop fs -cat "/data/raw/transactions/dt=2025-12-18/hour=14/part-*.jsonl" -First 1

# 4. Run pipeline
echo "=== RUNNING PIPELINE ==="
$start = Get-Date
$response = Invoke-WebRequest -Uri "http://localhost:8000/pipeline/run?dt=2025-12-18" -Method Post
$end = Get-Date
echo "Pipeline completed in $($end - $start)"

# 5. Check results in database
echo "=== RESULTS IN DATABASE ==="
docker exec postgres psql -U fraud_user -d frauddb -c "SELECT COUNT(*) FROM merchant_daily_metrics; SELECT COUNT(*) FROM alerts;"

# 6. Open dashboard
echo "=== OPENING DASHBOARD ==="
Start-Process "http://localhost:8501"
```

## Troubleshooting Quick Fixes

```powershell
# Services stuck? Full reset
docker-compose down -v --remove-orphans
docker container prune -f
docker-compose up -d

# Backend not starting? Check logs
docker logs backend

# HDFS safemode? Wait it out
docker exec namenode hadoop dfsadmin -safemode leave

# Database connection issues?
docker-compose restart postgres

# Kafka not connecting?
docker-compose restart kafka
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## Environment Variables

```powershell
# View .env file
cat .env

# Key settings to know:
# KAFKA_BOOTSTRAP_SERVERS=kafka:9092
# HDFS_URL=hdfs://namenode:9000
# POSTGRES_HOST=postgres
# DEFAULT_DATE=2025-12-18
# TRANSACTIONS_PER_BATCH=100
# BATCH_INTERVAL_SECONDS=10
```

---

**Pro Tips:**
1. Always check `docker-compose ps` first for service status
2. Use `docker logs` to debug issues before restarting
3. The pipeline takes ~90 seconds to complete
4. Data continues to flow even while pipeline runs
5. Dashboard auto-refreshes every page load
6. API docs at `/docs` are always up to date

**Common Wait Times:**
- Service startup: 2-3 minutes for all services healthy
- Data generation: Continuous (100 tx per 10 seconds)
- Pipeline execution: ~90 seconds total
- Data visible in dashboard: Immediate after pipeline completes

