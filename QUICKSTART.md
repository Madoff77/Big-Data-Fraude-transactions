# Quick Start Guide - Fraud Detection MVP

## 🚀 Launch Commands

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait 2-3 minutes for initialization

# 3. Check status
docker-compose ps

# 4. View logs (optional)
docker-compose logs -f producer consumer

# 5. Access dashboard
# Open browser: http://localhost:8501

# 6. Run pipeline (after data is generated)
curl -X POST "http://localhost:8000/pipeline/run?dt=2025-12-18"

# 7. View results in dashboard
# Navigate to Overview, Alerts, and Merchant Analytics pages
```

## 🔗 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:8501 | Main UI |
| **API** | http://localhost:8000 | Backend REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **HDFS** | http://localhost:9870 | HDFS Web UI |
| **YARN** | http://localhost:8088 | YARN Resource Manager |
| **PostgreSQL** | localhost:5432 | Database (user: fraud_user, db: frauddb) |

## 📊 Demo Flow

1. **Generate Data** (2-3 minutes)
   - Producer sends ~300 transactions to Kafka
   - Consumer writes to HDFS

2. **Verify Data in HDFS**
   ```bash
   docker exec -it namenode hadoop fs -ls /data/raw/transactions/dt=2025-12-18/
   ```

3. **Run Pipeline** (~90 seconds)
   - Via API: `curl -X POST "http://localhost:8000/pipeline/run?dt=2025-12-18"`
   - Or via dashboard: Pipeline Control page

4. **View Results**
   - Dashboard → Overview: See metrics and alerts summary
   - Dashboard → Alerts: Filter and view fraud alerts
   - Dashboard → Merchant Analytics: Top merchants and trends

## 🛠️ Useful Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Restart specific service
docker-compose restart producer

# View logs for specific service
docker-compose logs -f backend

# Access container shell
docker exec -it namenode bash
docker exec -it backend bash

# Check HDFS data
docker exec -it namenode hadoop fs -ls /data/
docker exec -it namenode hadoop fs -cat /data/raw/transactions/dt=2025-12-18/hour=*/part-*.jsonl | head

# Query PostgreSQL
docker exec -it postgres psql -U fraud_user -d frauddb -c "SELECT COUNT(*) FROM alerts;"

# Manual pipeline run
docker exec -it backend bash /app/scripts/run_pipeline.sh 2025-12-18
```

## ⚠️ Quick Troubleshooting

**Problem**: Services not starting
```bash
# Solution: Check Docker resources (need 8GB RAM minimum)
docker-compose down -v
docker-compose up -d
```

**Problem**: HDFS not accessible
```bash
# Solution: Wait for namenode initialization (2-3 min)
docker-compose logs namenode | grep "Safemode"
```

**Problem**: No data in dashboard
```bash
# Solution: Ensure pipeline has run
docker exec -it backend python3 /app/loader/load_to_postgres.py 2025-12-18
```

**Problem**: Pipeline fails
```bash
# Solution: Check HDFS has data
docker exec -it namenode hadoop fs -ls /data/raw/transactions/dt=2025-12-18/
```

## 📋 Health Checks

```bash
# All services status
docker-compose ps

# Backend health
curl http://localhost:8000/health

# HDFS health
curl http://localhost:9870

# YARN health  
curl http://localhost:8088

# Check data exists
docker exec -it namenode hadoop fs -du -h /data/raw/transactions/

# Check database
docker exec -it postgres psql -U fraud_user -d frauddb -c "\dt"
```

## 🎯 Key Metrics to Show in Demo

1. **Total Transactions**: ~300-1000 (depends on how long producer runs)
2. **Merchants**: ~50 unique merchants
3. **Alerts**: ~5-15 fraud alerts generated
4. **Top Rules**: HIGH_AMOUNT, BURST most common
5. **Processing Time**: ~90 seconds for full pipeline

## 📝 Notes

- Default date: `2025-12-18` (configurable in `.env`)
- Transaction generation: 100 per batch, every 10 seconds
- Let producer run 2-3 minutes before running pipeline
- Pipeline is idempotent - can re-run safely
- All data is partitioned by date and hour in HDFS

## 🎓 For Presentation

**Key Points to Highlight:**
1. ✅ All mandatory technologies: HDFS, MapReduce, Kafka, PostgreSQL, Frontend, Backend
2. ✅ End-to-end pipeline: Ingestion → Processing → Storage → API → Visualization
3. ✅ Open-source only: No proprietary tech
4. ✅ Docker Compose: Single command to run everything
5. ✅ Demonstrable: Live dashboard with real-time data

**Architecture Flow:**
Producer → Kafka → Consumer → HDFS → MapReduce (3 jobs) → PostgreSQL → FastAPI → Streamlit

**Fraud Detection Rules:**
- HIGH_AMOUNT: Transaction > $1000
- BURST: > 30 transactions/day
- MULTI_COUNTRY: >= 3 countries
- HIGH_DECLINE: > 50% decline rate

Good luck! 🚀
