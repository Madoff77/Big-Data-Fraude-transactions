#!/usr/bin/env python3
"""
Kafka Consumer - Reads transactions and writes micro-batched JSONL files to HDFS
Partitioned by: /data/raw/transactions/dt=YYYY-MM-DD/hour=HH/part-<uuid>.jsonl
"""
import json
import os
import logging
from datetime import datetime
from uuid import uuid4
from kafka import KafkaConsumer
from hdfs import InsecureClient
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'transactions')
HDFS_URL = os.getenv('HDFS_URL', 'hdfs://namenode:9000')
HDFS_NAMENODE_HOST = HDFS_URL.replace('hdfs://', '').split(':')[0]
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))  # Write after N messages


def get_partition_path(timestamp_str):
    """
    Extract dt and hour from ISO timestamp and build HDFS partition path
    Example: 2025-12-18T14:30:00Z -> /data/raw/transactions/dt=2025-12-18/hour=14/
    """
    ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    dt = ts.strftime('%Y-%m-%d')
    hour = ts.strftime('%H')
    return f"/data/raw/transactions/dt={dt}/hour={hour}"


def write_batch_to_hdfs(hdfs_client, batch, partition_path):
    """Write a batch of transactions to HDFS as JSONL"""
    if not batch:
        return
    
    # Generate unique part file name
    part_filename = f"part-{uuid4()}.jsonl"
    full_path = f"{partition_path}/{part_filename}"
    
    # Prepare JSONL content
    jsonl_content = "\n".join([json.dumps(txn) for txn in batch]) + "\n"
    
    try:
        # Ensure directory exists (hdfs library creates parent dirs automatically)
        hdfs_client.write(full_path, jsonl_content.encode('utf-8'), overwrite=False)
        logger.info(f"Written {len(batch)} transactions to {full_path}")
    except Exception as e:
        logger.error(f"Failed to write to HDFS: {e}", exc_info=True)
        raise


def main():
    """Main consumer loop"""
    logger.info(f"Starting consumer - connecting to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"HDFS URL: {HDFS_URL}")
    
    # Initialize HDFS client
    hdfs_client = InsecureClient(f"http://{HDFS_NAMENODE_HOST}:9870", user='root')
    logger.info("Connected to HDFS")
    
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='hdfs-consumer-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    logger.info(f"Subscribed to topic: {KAFKA_TOPIC}")
    
    # Batch accumulator - grouped by partition path
    batches = {}
    total_consumed = 0
    
    try:
        for message in consumer:
            transaction = message.value
            total_consumed += 1
            
            # Determine partition path based on timestamp
            partition_path = get_partition_path(transaction['ts'])
            
            # Add to batch
            if partition_path not in batches:
                batches[partition_path] = []
            batches[partition_path].append(transaction)
            
            # Write batch if size threshold reached
            if len(batches[partition_path]) >= BATCH_SIZE:
                write_batch_to_hdfs(hdfs_client, batches[partition_path], partition_path)
                batches[partition_path] = []
            
            if total_consumed % 100 == 0:
                logger.info(f"Consumed {total_consumed} transactions")
                
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Error in consumer: {e}", exc_info=True)
    finally:
        # Flush remaining batches
        for partition_path, batch in batches.items():
            if batch:
                write_batch_to_hdfs(hdfs_client, batch, partition_path)
        
        consumer.close()
        logger.info(f"Consumer closed. Total consumed: {total_consumed}")


if __name__ == '__main__':
    main()
