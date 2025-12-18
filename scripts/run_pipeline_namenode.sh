#!/bin/bash
# Alternative Pipeline Script - Run directly from namenode container
# This script can be executed inside the namenode container which already has Hadoop configured
# Usage: docker exec namenode bash /path/to/this/script.sh 2025-12-18

set -e

DATE=${1:-2025-12-18}

echo "=========================================="
echo "Starting Pipeline for Date: $DATE"
echo "Running from namenode container"
echo "=========================================="

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
hadoop fs -du -h $RAW_INPUT | head -5

echo ""
echo "Step 2: Cleaning output directories (idempotency)..."
hadoop fs -rm -r -f $CLEAN_OUTPUT
hadoop fs -rm -r -f $METRICS_OUTPUT
hadoop fs -rm -r -f $ALERTS_OUTPUT

# Copy MapReduce scripts to namenode if needed
# They should be mounted via docker-compose volumes

echo ""
echo "=========================================="
echo "MR1: clean_normalize"
echo "=========================================="
echo "Input: $RAW_INPUT"
echo "Output: $CLEAN_OUTPUT"

hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input $RAW_INPUT \
    -output $CLEAN_OUTPUT \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -file /mapreduce/clean_normalize/mapper.py \
    -file /mapreduce/clean_normalize/reducer.py

echo "MR1 Complete!"

echo ""
echo "=========================================="
echo "MR2: merchant_daily_metrics"
echo "=========================================="

hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input $CLEAN_OUTPUT \
    -output $METRICS_OUTPUT \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -file /mapreduce/merchant_metrics/mapper.py \
    -file /mapreduce/merchant_metrics/reducer.py

echo "MR2 Complete!"

echo ""
echo "=========================================="
echo "MR3: alerts_generation"
echo "=========================================="

hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input $METRICS_OUTPUT \
    -output $ALERTS_OUTPUT \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -file /mapreduce/alerts/mapper.py \
    -file /mapreduce/alerts/reducer.py

echo "MR3 Complete!"

echo ""
echo "=========================================="
echo "Pipeline Complete!"
echo "=========================================="
echo "Date: $DATE"
echo "Results in HDFS:"
echo "  - Clean data: $CLEAN_OUTPUT"
echo "  - Metrics: $METRICS_OUTPUT"
echo "  - Alerts: $ALERTS_OUTPUT"
