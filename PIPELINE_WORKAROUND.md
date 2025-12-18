# Pipeline Execution Workaround

## Issue
Backend container is missing JAVA_HOME environment variable, causing MapReduce jobs to fail.

## Immediate Solution: Run from Namenode Container

The namenode container already has Hadoop fully configured. You can run the pipeline directly from there:

### Step 1: Copy MapReduce scripts to namenode

```powershell
# Copy scripts
docker cp ./mapreduce namenode:/
docker cp ./scripts/run_pipeline_namenode.sh namenode:/scripts/
```

### Step 2: Run the pipeline

```powershell
docker exec namenode bash /scripts/run_pipeline_namenode.sh 2025-12-18
```

### Step 3: Load data to PostgreSQL manually

After MapReduce completes:

```powershell
# Enter backend container
docker exec -it backend bash

# Run loader
cd /app
python3 loader/load_to_postgres.py 2025-12-18
```

## Alternative: Wait for Backend Rebuild

The backend is currently rebuilding with JAVA_HOME properly set. This will take ~2-3 minutes to complete.

Once done, the API endpoint will work:
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/pipeline/run?dt=2025-12-18" -Method Post
```

## Quick Manual Pipeline Steps

If you want to run it step by step right now:

```powershell
# 1. Enter namenode
docker exec -it namenode bash

# 2. Inside namenode, run MR1 (Clean & Normalize)
hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input /data/raw/transactions/dt=2025-12-18 \
    -output /data/curated/transactions_clean/dt=2025-12-18 \
    -mapper "python3 /mapreduce/clean_normalize/mapper.py" \
    -reducer "python3 /mapreduce/clean_normalize/reducer.py" \
    -file /mapreduce/clean_normalize/mapper.py \
    -file /mapreduce/clean_normalize/reducer.py

# 3. Run MR2 (Merchant Metrics)
hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input /data/curated/transactions_clean/dt=2025-12-18 \
    -output /data/marts/merchant_daily_metrics/dt=2025-12-18 \
    -mapper "python3 /mapreduce/merchant_metrics/mapper.py" \
    -reducer "python3 /mapreduce/merchant_metrics/reducer.py" \
    -file /mapreduce/merchant_metrics/mapper.py \
    -file /mapreduce/merchant_metrics/reducer.py

# 4. Run MR3 (Alerts)
hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input /data/marts/merchant_daily_metrics/dt=2025-12-18 \
    -output /data/marts/alerts/dt=2025-12-18 \
    -mapper "python3 /mapreduce/alerts/mapper.py" \
    -reducer "python3 /mapreduce/alerts/reducer.py" \
    -file /mapreduce/alerts/mapper.py \
    -file /mapreduce/alerts/reducer.py

# 5. Exit namenode
exit

# 6. Load to PostgreSQL
docker exec backend python3 /app/loader/load_to_postgres.py 2025-12-18
```

## Status Check

```powershell
# Check if backend rebuild is done
docker ps --filter "name=backend"

# Check backend logs
docker logs backend --tail 5
```

Once backend shows "Uvicorn running", the API method will work again.
