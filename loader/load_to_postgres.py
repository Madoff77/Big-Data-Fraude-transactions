#!/usr/bin/env python3
"""
Loader - Loads merchant metrics and alerts from HDFS to PostgreSQL
"""
import os
import sys
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch
from hdfs import InsecureClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'frauddb')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'fraud_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'fraud_password_123')

HDFS_URL = os.getenv('HDFS_URL', 'hdfs://namenode:9000')
HDFS_NAMENODE_HOST = HDFS_URL.replace('hdfs://', '').split(':')[0]


def get_db_connection():
    """Create PostgreSQL connection"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    return conn


def load_merchant_metrics(hdfs_client, dt):
    """Load merchant daily metrics from HDFS for given date"""
    metrics_path = f"/data/marts/merchant_daily_metrics/dt={dt}"
    
    try:
        files = hdfs_client.list(metrics_path)
    except Exception as e:
        logger.error(f"Failed to list files in {metrics_path}: {e}")
        return []
    
    all_metrics = []
    
    for filename in files:
        if filename.startswith('part-'):
            file_path = f"{metrics_path}/{filename}"
            logger.info(f"Reading {file_path}")
            
            try:
                with hdfs_client.read(file_path, encoding='utf-8') as reader:
                    for line in reader:
                        line = line.strip()
                        if not line:
                            continue
                        
                        parts = line.split('\t')
                        if len(parts) < 9:
                            continue
                        
                        metric = {
                            'dt': parts[0],
                            'merchant_id': parts[1],
                            'tx_count': int(parts[2]),
                            'sum_amount': float(parts[3]),
                            'avg_amount': float(parts[4]),
                            'max_amount': float(parts[5]),
                            'unique_countries': int(parts[6]),
                            'unique_devices': int(parts[7]),
                            'decline_rate': float(parts[8])
                        }
                        all_metrics.append(metric)
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
    
    logger.info(f"Loaded {len(all_metrics)} metrics from HDFS")
    return all_metrics


def load_alerts(hdfs_client, dt):
    """Load alerts from HDFS for given date"""
    alerts_path = f"/data/marts/alerts/dt={dt}"
    
    try:
        files = hdfs_client.list(alerts_path)
    except Exception as e:
        logger.error(f"Failed to list files in {alerts_path}: {e}")
        return []
    
    all_alerts = []
    
    for filename in files:
        if filename.startswith('part-'):
            file_path = f"{alerts_path}/{filename}"
            logger.info(f"Reading {file_path}")
            
            try:
                with hdfs_client.read(file_path, encoding='utf-8') as reader:
                    for line in reader:
                        line = line.strip()
                        if not line:
                            continue
                        
                        alert = json.loads(line)
                        all_alerts.append(alert)
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
    
    logger.info(f"Loaded {len(all_alerts)} alerts from HDFS")
    return all_alerts


def insert_metrics(conn, metrics):
    """Insert metrics into PostgreSQL with UPSERT"""
    if not metrics:
        logger.info("No metrics to insert")
        return
    
    cursor = conn.cursor()
    
    # Delete existing records for this date range (cast strings to dates)
    dts = list(set([m['dt'] for m in metrics]))
    cursor.execute("DELETE FROM merchant_daily_metrics WHERE dt = ANY(%s::date[])", (dts,))
    
    # Insert new records
    insert_sql = """
        INSERT INTO merchant_daily_metrics 
        (dt, merchant_id, tx_count, sum_amount, avg_amount, max_amount, 
         unique_countries, unique_devices, decline_rate)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (dt, merchant_id) DO UPDATE SET
            tx_count = EXCLUDED.tx_count,
            sum_amount = EXCLUDED.sum_amount,
            avg_amount = EXCLUDED.avg_amount,
            max_amount = EXCLUDED.max_amount,
            unique_countries = EXCLUDED.unique_countries,
            unique_devices = EXCLUDED.unique_devices,
            decline_rate = EXCLUDED.decline_rate
    """
    
    data = [
        (m['dt'], m['merchant_id'], m['tx_count'], m['sum_amount'], 
         m['avg_amount'], m['max_amount'], m['unique_countries'], 
         m['unique_devices'], m['decline_rate'])
        for m in metrics
    ]
    
    execute_batch(cursor, insert_sql, data)
    conn.commit()
    logger.info(f"Inserted {len(metrics)} metrics into PostgreSQL")


def insert_alerts(conn, alerts):
    """Insert alerts into PostgreSQL"""
    if not alerts:
        logger.info("No alerts to insert")
        return
    
    cursor = conn.cursor()
    
    # Delete existing alerts for this date range (cast strings to dates)
    dts = list(set([a['dt'] for a in alerts]))
    cursor.execute("DELETE FROM alerts WHERE dt = ANY(%s::date[])", (dts,))
    
    # Insert new alerts
    insert_sql = """
        INSERT INTO alerts 
        (dt, merchant_id, customer_id, rule_code, severity, details)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    data = [
        (a['dt'], a.get('merchant_id'), a.get('customer_id'), 
         a['rule_code'], a['severity'], json.dumps(a['details']))
        for a in alerts
    ]
    
    execute_batch(cursor, insert_sql, data)
    conn.commit()
    logger.info(f"Inserted {len(alerts)} alerts into PostgreSQL")


def main():
    """Main loader function"""
    if len(sys.argv) < 2:
        logger.error("Usage: python load_to_postgres.py <date>")
        logger.error("Example: python load_to_postgres.py 2025-12-18")
        sys.exit(1)
    
    dt = sys.argv[1]
    logger.info(f"Loading data for date: {dt}")
    
    # Connect to HDFS
    hdfs_client = InsecureClient(f"http://{HDFS_NAMENODE_HOST}:9870", user='root')
    logger.info("Connected to HDFS")
    
    # Load data from HDFS
    metrics = load_merchant_metrics(hdfs_client, dt)
    alerts = load_alerts(hdfs_client, dt)
    
    # Connect to PostgreSQL
    conn = get_db_connection()
    logger.info("Connected to PostgreSQL")
    
    # Insert data
    insert_metrics(conn, metrics)
    insert_alerts(conn, alerts)
    
    conn.close()
    logger.info("Load complete!")


if __name__ == '__main__':
    main()
