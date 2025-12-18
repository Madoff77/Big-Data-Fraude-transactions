#!/bin/bash
# Pipeline execution script - runs all MapReduce jobs and loads data to PostgreSQL
# Usage: ./run_pipeline.sh <date>
# Example: ./run_pipeline.sh 2025-12-18

set -e

DATE=${1:-2025-12-18}

echo "=========================================="
echo "Starting Pipeline for Date: $DATE"
echo "=========================================="

# Extract hour from date (default to all hours if not specified)
YEAR=$(echo $DATE | cut -d'-' -f1)
MONTH=$(echo $DATE | cut -d'-' -f2)
DAY=$(echo $DATE | cut -d'-' -f3)

# HDFS paths
RAW_INPUT="/data/raw/transactions/dt=${DATE}"
CLEAN_OUTPUT="/data/curated/transactions_clean/dt=${DATE}"
METRICS_OUTPUT="/data/marts/merchant_daily_metrics/dt=${DATE}"
ALERTS_OUTPUT="/data/marts/alerts/dt=${DATE}"

echo ""
echo "Step 0: Creating HDFS directories..."
hadoop fs -mkdir -p /data/raw/transactions
hadoop fs -mkdir -p /data/curated/transactions_clean
hadoop fs -mkdir -p /data/marts/merchant_daily_metrics
hadoop fs -mkdir -p /data/marts/alerts

echo ""
echo "Step 1: Checking input data..."
if ! hadoop fs -test -d $RAW_INPUT; then
    echo "ERROR: Input directory $RAW_INPUT does not exist!"
    echo "Make sure producer and consumer have generated data for this date."
    exit 1
fi

echo "Input data found at $RAW_INPUT"
hadoop fs -du -h $RAW_INPUT

echo ""
echo "Step 2: Cleaning output directories (idempotency)..."
hadoop fs -rm -r -f $CLEAN_OUTPUT
hadoop fs -rm -r -f $METRICS_OUTPUT
hadoop fs -rm -r -f $ALERTS_OUTPUT

echo ""
echo "=========================================="
echo "MR1: clean_normalize"
echo "=========================================="
echo "Input: $RAW_INPUT"
echo "Output: $CLEAN_OUTPUT"

hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -D mapreduce.task.timeout=600000 \
    -D mapreduce.reduce.memory.mb=1024 \
    -D mapreduce.map.memory.mb=1024 \
    -input $RAW_INPUT/hour=*/part-*.jsonl \
    -output $CLEAN_OUTPUT \
    -mapper "python3 /app/mapreduce/clean_normalize/mapper.py" \
    -reducer "python3 /app/mapreduce/clean_normalize/reducer.py" \
    -file /app/mapreduce/clean_normalize/mapper.py \
    -file /app/mapreduce/clean_normalize/reducer.py

echo "MR1 Complete!"
echo "Output:"
hadoop fs -du -h $CLEAN_OUTPUT

echo ""
echo "=========================================="
echo "MR2: merchant_daily_metrics"
echo "=========================================="
echo "Input: $CLEAN_OUTPUT"
echo "Output: $METRICS_OUTPUT"

hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input $CLEAN_OUTPUT \
    -output $METRICS_OUTPUT \
    -mapper "python3 /app/mapreduce/merchant_metrics/mapper.py" \
    -reducer "python3 /app/mapreduce/merchant_metrics/reducer.py" \
    -file /app/mapreduce/merchant_metrics/mapper.py \
    -file /app/mapreduce/merchant_metrics/reducer.py

echo "MR2 Complete!"
echo "Output:"
hadoop fs -du -h $METRICS_OUTPUT

echo ""
echo "=========================================="
echo "MR3: alerts_generation"
echo "=========================================="
echo "Input: $METRICS_OUTPUT"
echo "Output: $ALERTS_OUTPUT"

hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input $METRICS_OUTPUT \
    -output $ALERTS_OUTPUT \
    -mapper "python3 /app/mapreduce/alerts/mapper.py" \
    -reducer "python3 /app/mapreduce/alerts/reducer.py" \
    -file /app/mapreduce/alerts/mapper.py \
    -file /app/mapreduce/alerts/reducer.py

echo "MR3 Complete!"
echo "Output:"
hadoop fs -du -h $ALERTS_OUTPUT

echo ""
echo "=========================================="
echo "Step 3: Loading data to PostgreSQL"
echo "=========================================="

python3 /app/loader/load_to_postgres.py $DATE

echo ""
echo "=========================================="
echo "Pipeline Complete!"
echo "=========================================="
echo "Date: $DATE"
echo "All data loaded to PostgreSQL successfully."
