# Big Data Fraud Detection System

![Architecture](https://img.shields.io/badge/Architecture-Big%20Data-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.10-yellow)

A complete end-to-end Big Data architecture for real-time transaction monitoring and fraud risk detection using open-source technologies.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technologies](#technologies)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Running the Demo](#running-the-demo)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

## Overview

This project implements a scalable fraud detection system that:
- Ingests real-time transaction data via **Kafka**
- Stores raw data in **HDFS** with partitioning
- Processes data using **Hadoop MapReduce** (3 jobs)
- Stores aggregated results in **PostgreSQL**
- Exposes data via **FastAPI** REST API
- Visualizes insights through **Streamlit** dashboard

### Key Features

- Real-time streaming with Kafka
- Big Data storage with HDFS
- Batch processing with MapReduce (Python streaming)
- Relational database integration (PostgreSQL)
- RESTful API backend (FastAPI)
- Interactive dashboard (Streamlit)
- Fully containerized with Docker Compose
- Rule-based fraud detection (4 alert rules)

##  Architecture

### High-Level Architecture

```
┌─────────────┐      ┌─────────┐      ┌──────────────┐
│   Producer  │─────▶│  Kafka  │─────▶│   Consumer   │
│  (Synthetic)│      │ (Topic) │      │ (to HDFS)    │
└─────────────┘      └─────────┘      └──────┬───────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────┐
│                    HDFS Storage                     │
│  /data/raw/transactions/dt=YYYY-MM-DD/hour=HH/      │
└───────────────────────┬─────────────────────────────┘
                        │
            ┌───────────▼──────────┐
            │   MapReduce Jobs     │
            │  ┌──────────────┐   │
            │  │ MR1: Clean   │   │
            │  │ & Normalize  │   │
            │  └──────┬───────┘   │
            │         │            │
            │  ┌──────▼───────┐   │
            │  │ MR2: Merchant│   │
            │  │   Metrics    │   │
            │  └──────┬───────┘   │
            │         │            │
            │  ┌──────▼───────┐   │
            │  │ MR3: Alerts  │   │
            │  │  Generation  │   │
            │  └──────┬───────┘   │
            └─────────┼───────────┘
                      │
            ┌─────────▼──────────┐
            │    Loader Script   │
            └─────────┬──────────┘
                      │
            ┌─────────▼──────────┐
            │    PostgreSQL      │
            │  - Metrics Tables  │
            │  - Alerts Tables   │
            └─────────┬──────────┘
                      │
            ┌─────────▼──────────┐
            │   FastAPI Backend  │
            │   - REST Endpoints │
            └─────────┬──────────┘
                      │
            ┌─────────▼──────────┐
            │ Streamlit Frontend │
            │    - Dashboard     │
            └────────────────────┘
```

### Data Flow

1. **Ingestion**: Producer generates synthetic transactions → Kafka topic
2. **Streaming**: Consumer reads from Kafka → writes JSONL to HDFS (partitioned by date/hour)
3. **Processing**:
   - **MR1**: Cleans and normalizes JSON → TSV format
   - **MR2**: Aggregates by merchant/date → computes metrics
   - **MR3**: Applies fraud rules → generates alerts
4. **Storage**: Loader reads HDFS output → writes to PostgreSQL
5. **API**: FastAPI serves data from PostgreSQL
6. **Visualization**: Streamlit dashboard queries API → displays insights

##  Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Streaming** | Apache Kafka | Real-time message ingestion |
| **Storage** | HDFS (Hadoop 3.2.1) | Distributed file storage |
| **Processing** | MapReduce (Hadoop Streaming) | Batch data processing |
| **Database** | PostgreSQL 15 | Relational data storage |
| **Backend** | FastAPI | REST API service |
| **Frontend** | Streamlit | Web dashboard |
| **Orchestration** | Docker Compose | Container management |

##  Prerequisites

- **Docker Desktop** (20.10+)
- **Docker Compose** (2.0+)
- **8GB RAM minimum** (16GB recommended)
- **20GB free disk space**

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum (Hadoop requires memory)
- **OS**: Windows 10/11, macOS, or Linux

##  Quick Start

### 1. Clone or Create Project Directory

```bash
cd Big_Data_Fraude
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will start:
- Zookeeper
- Kafka
- Hadoop (NameNode, DataNode, ResourceManager, NodeManager)
- PostgreSQL
- Producer (generates transactions)
- Consumer (writes to HDFS)
- Backend API
- Frontend Dashboard

### 3. Wait for Services to Initialize

```bash
# Check service status
docker-compose ps

# View logs (optional)
docker-compose logs -f
```

**Note**: Hadoop services may take 2-3 minutes to fully initialize.

### 4. Access the Dashboard

Open your browser:
```
http://localhost:8501
```

### 5. Run the Pipeline

Via API (using curl or Postman):
```bash
curl -X POST "http://localhost:8000/pipeline/run?dt=2025-12-18"
```

Or use the "Pipeline Control" page in the dashboard.

### 6. View Results

Navigate through the dashboard to see:
- Overview metrics
- Fraud alerts
- Top merchants
- Time series analytics

##  Detailed Setup

### Step-by-Step Instructions

#### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` if needed (default values work for local setup).

#### 2. Start Infrastructure Services

```bash
# Start Kafka and Hadoop first
docker-compose up -d zookeeper kafka namenode datanode resourcemanager nodemanager postgres
```

Wait for services to be healthy:
```bash
docker-compose ps
```

#### 3. Verify HDFS

```bash
# Access namenode container
docker exec -it namenode bash

# Check HDFS
hadoop fs -ls /

# Exit
exit
```

#### 4. Start Data Pipeline Services

```bash
docker-compose up -d producer consumer
```

Check logs to verify data flow:
```bash
docker-compose logs -f producer
docker-compose logs -f consumer
```

You should see:
- Producer: "Batch X sent (100 transactions)"
- Consumer: "Written N transactions to HDFS..."

#### 5. Start Application Services

```bash
docker-compose up -d backend frontend
```

#### 6. Verify Backend API

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "database": "connected"
}
```

#### 7. Access Services

- **Frontend Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **HDFS Web UI**: http://localhost:9870
- **YARN Web UI**: http://localhost:8088

##  Running the Demo

### Scenario: Process One Day of Transactions

#### Step 1: Generate Data (Automatic)

The producer automatically generates transactions for `2025-12-18` (configurable via `.env`).

Let it run for 2-3 minutes to generate sufficient data (~1000+ transactions).

#### Step 2: Verify Data in HDFS

```bash
docker exec -it namenode bash
hadoop fs -ls /data/raw/transactions/dt=2025-12-18/
hadoop fs -cat /data/raw/transactions/dt=2025-12-18/hour=*/part-*.jsonl | head -n 5
exit
```

#### Step 3: Run MapReduce Pipeline

**Option A: Via API**
```bash
curl -X POST "http://localhost:8000/pipeline/run?dt=2025-12-18"
```

**Option B: Via Dashboard**
1. Navigate to "Pipeline Control"
2. Select date: 2025-12-18
3. Click "Run Pipeline"

**Option C: Manually in Container**
```bash
docker exec -it backend bash
bash /app/scripts/run_pipeline.sh 2025-12-18
exit
```

#### Step 4: Monitor Pipeline Execution

The pipeline executes 3 MapReduce jobs:
1. **MR1**: Clean & normalize (~30 seconds)
2. **MR2**: Compute merchant metrics (~30 seconds)
3. **MR3**: Generate alerts (~20 seconds)
4. **Load to PostgreSQL** (~5 seconds)

Total time: ~90 seconds

#### Step 5: Explore Dashboard

1. **Overview Page**:
   - View total merchants, transactions, amounts
   - See alert distribution
   - Check rule breakdown

2. **Alerts Page**:
   - Filter by severity (1-3)
   - Filter by rule code
   - View alert details

3. **Merchant Analytics**:
   - View top merchants by various metrics
   - Load time series for specific merchants

#### Step 6: Query API Directly

**Get top merchants:**
```bash
curl "http://localhost:8000/metrics/merchants/top?dt=2025-12-18&metric=tx_count&n=10"
```

**Get alerts:**
```bash
curl "http://localhost:8000/alerts?dt=2025-12-18&severity_min=3"
```

**Get merchant time series:**
```bash
curl "http://localhost:8000/merchant/MERCHANT_0001/series?from=2025-12-18&to=2025-12-18"
```

##  API Documentation

### Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics/merchants/top` | Top N merchants by metric |
| GET | `/alerts` | Get alerts with filters |
| GET | `/merchant/{id}/series` | Time series for merchant |
| POST | `/pipeline/run` | Trigger MapReduce pipeline |
| GET | `/stats/summary` | Summary statistics |

### API Examples

**Top Merchants:**
```bash
GET /metrics/merchants/top?dt=2025-12-18&metric=tx_count&n=10
```

**Filtered Alerts:**
```bash
GET /alerts?dt=2025-12-18&severity_min=2&rule_code=HIGH_AMOUNT
```

**Run Pipeline:**
```bash
POST /pipeline/run?dt=2025-12-18
```

Full interactive documentation: http://localhost:8000/docs

## 📁 Project Structure

```
Big_Data_Fraude/
├── docker-compose.yml          # Orchestration
├── .env.example                # Configuration template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
│
├── producer/                   # Kafka producer
│   ├── producer.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── consumer/                   # Kafka consumer
│   ├── consumer_to_hdfs.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── mapreduce/                  # MapReduce jobs
│   ├── clean_normalize/
│   │   ├── mapper.py
│   │   └── reducer.py
│   ├── merchant_metrics/
│   │   ├── mapper.py
│   │   └── reducer.py
│   └── alerts/
│       ├── mapper.py
│       └── reducer.py
│
├── loader/                     # HDFS to PostgreSQL
│   ├── load_to_postgres.py
│   └── requirements.txt
│
├── scripts/                    # Pipeline scripts
│   └── run_pipeline.sh
│
├── sql/                        # Database schemas
│   └── init.sql
│
├── backend/                    # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/                   # Streamlit frontend
    ├── app.py
    ├── requirements.txt
    └── Dockerfile
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Hadoop Services Not Starting

**Symptoms**: NameNode or DataNode fails to start

**Solutions**:
```bash
# Remove volumes and restart
docker-compose down -v
docker-compose up -d namenode datanode

# Check logs
docker-compose logs namenode
```

#### 2. Kafka Connection Issues

**Symptoms**: Producer/Consumer can't connect to Kafka

**Solutions**:
```bash
# Ensure Kafka is healthy
docker-compose ps kafka

# Restart Kafka
docker-compose restart kafka

# Check broker is ready
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
```

#### 3. HDFS WebHDFS Errors

**Symptoms**: Consumer fails with HDFS connection errors

**Solutions**:
```bash
# Verify HDFS web interface
curl http://localhost:9870

# Test HDFS from namenode
docker exec -it namenode hadoop fs -ls /

# Check WebHDFS is enabled
docker exec -it namenode cat /opt/hadoop/etc/hadoop/hdfs-site.xml | grep webhdfs
```

#### 4. MapReduce Job Failures

**Symptoms**: Pipeline fails during MR execution

**Solutions**:
```bash
# Check YARN ResourceManager
curl http://localhost:8088

# View job logs in YARN UI
# http://localhost:8088/cluster/apps

# Run MR job manually with verbose output
docker exec -it backend bash
hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar -help
```

#### 5. PostgreSQL Connection Errors

**Symptoms**: Backend can't connect to database

**Solutions**:
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Test connection
docker exec -it postgres psql -U fraud_user -d frauddb -c "SELECT 1;"

# Check tables
docker exec -it postgres psql -U fraud_user -d frauddb -c "\dt"
```

#### 6. Out of Memory Errors

**Symptoms**: Services crash or containers restart

**Solutions**:
- Increase Docker Desktop memory allocation (Settings → Resources → Memory)
- Reduce batch sizes in `.env`:
  ```
  TRANSACTIONS_PER_BATCH=50
  BATCH_SIZE=25
  ```
- Stop unused services temporarily

#### 7. Port Conflicts

**Symptoms**: "Port already in use" error

**Solutions**:
```bash
# Check which process is using the port (example for port 8000)
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Change ports in docker-compose.yml if needed
```

### Debug Commands

**View all logs:**
```bash
docker-compose logs -f
```

**View specific service logs:**
```bash
docker-compose logs -f producer
docker-compose logs -f backend
```

**Execute commands in containers:**
```bash
# Check HDFS
docker exec -it namenode hadoop fs -ls /data/

# Check Kafka topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Query PostgreSQL
docker exec -it postgres psql -U fraud_user -d frauddb
```

**Reset everything:**
```bash
docker-compose down -v
docker-compose up -d
```

##  Architecture Explanation

### Why These Technologies?

#### Kafka
- **Purpose**: Real-time data ingestion
- **Why**: Industry standard for streaming, handles high throughput, guarantees message delivery
- **Alternative**: RabbitMQ, AWS Kinesis (but not open-source)

#### HDFS
- **Purpose**: Distributed storage for Big Data
- **Why**: Fault-tolerant, scales horizontally, integrates with Hadoop ecosystem
- **Alternative**: S3, GCS (but not open-source)

#### MapReduce
- **Purpose**: Parallel batch processing
- **Why**: Proven for large-scale data processing, fault-tolerant, works with HDFS
- **Alternative**: Spark (but MapReduce is simpler for this MVP)

#### PostgreSQL
- **Purpose**: Structured data storage and analytics
- **Why**: ACID compliance, excellent for aggregated metrics, supports JSON
- **Alternative**: MySQL, MongoDB

#### FastAPI
- **Purpose**: Modern REST API framework
- **Why**: Fast, automatic API docs, async support, type hints
- **Alternative**: Flask, Django

#### Streamlit
- **Purpose**: Rapid dashboard development
- **Why**: Python-native, minimal code, reactive UI
- **Alternative**: React, Vue (but requires more development time)

### Fraud Detection Rules

The system implements 4 rule-based alerts:

1. **HIGH_AMOUNT** (Severity: 3)
   - Trigger: Maximum transaction > $1000
   - Rationale: Large transactions are high-risk

2. **BURST** (Severity: 2)
   - Trigger: More than 30 transactions per day
   - Rationale: Unusual activity volume

3. **MULTI_COUNTRY** (Severity: 2)
   - Trigger: Transactions from 3+ countries
   - Rationale: Geographic anomaly

4. **HIGH_DECLINE** (Severity: 3)
   - Trigger: Decline rate > 50%
   - Rationale: Payment issues or testing

### Scalability Considerations

**Current Setup (MVP)**:
- Single-node Hadoop (pseudo-distributed)
- Single Kafka broker
- ~1000 transactions/minute

**Production Scaling**:
- Multi-node Hadoop cluster (3+ nodes)
- Kafka cluster (3+ brokers)
- Horizontal scaling of consumers
- Database replication
- Load balancer for API

##  License

MIT License - feel free to use for educational purposes.

##  Contributing

This is an educational project for a Master's degree. Feedback and suggestions are welcome!

##  Contact

For questions or issues, please create an issue in the repository.

---

**Good luck! **

