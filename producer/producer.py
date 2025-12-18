#!/usr/bin/env python3
"""
Kafka Producer - Generates synthetic transaction events
"""
import json
import random
import uuid
from datetime import datetime, timedelta
from time import sleep
import os
import logging
from kafka import KafkaProducer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'transactions')
TRANSACTIONS_PER_BATCH = int(os.getenv('TRANSACTIONS_PER_BATCH', '100'))
BATCH_INTERVAL_SECONDS = int(os.getenv('BATCH_INTERVAL_SECONDS', '10'))
DEFAULT_DATE = os.getenv('DEFAULT_DATE', '2025-12-18')

# Static data pools for synthetic generation
MERCHANTS = [f"MERCHANT_{i:04d}" for i in range(1, 51)]
CUSTOMERS = [f"CUSTOMER_{i:05d}" for i in range(1, 501)]
COUNTRIES = ['US', 'GB', 'FR', 'DE', 'ES', 'IT', 'CA', 'AU', 'JP', 'BR', 'IN', 'MX']
CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']
PAYMENT_METHODS = ['CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'BANK_TRANSFER', 'CRYPTO']
STATUSES = ['APPROVED', 'DECLINED']


def generate_transaction(target_date=None):
    """Generate a single synthetic transaction"""
    if target_date:
        # Parse target date and generate timestamp within that day
        base_dt = datetime.strptime(target_date, '%Y-%m-%d')
        # Random hour and minute within the day
        random_seconds = random.randint(0, 86399)  # 0 to 23:59:59
        ts = base_dt + timedelta(seconds=random_seconds)
    else:
        ts = datetime.utcnow()
    
    # Generate transaction with some patterns for fraud detection
    merchant_id = random.choice(MERCHANTS)
    customer_id = random.choice(CUSTOMERS)
    
    # Base amount distribution
    if random.random() < 0.05:  # 5% high value (potential HIGH_AMOUNT alerts)
        amount = round(random.uniform(1000, 5000), 2)
    else:
        amount = round(random.uniform(5, 500), 2)
    
    # Country distribution - some merchants/customers are multi-country
    country = random.choice(COUNTRIES)
    
    # Status distribution - 10% declined
    status = 'DECLINED' if random.random() < 0.1 else 'APPROVED'
    
    transaction = {
        'tx_id': str(uuid.uuid4()),
        'ts': ts.isoformat() + 'Z',
        'customer_id': customer_id,
        'merchant_id': merchant_id,
        'country': country,
        'amount': amount,
        'currency': random.choice(CURRENCIES),
        'payment_method': random.choice(PAYMENT_METHODS),
        'device_id': f"DEVICE_{random.randint(1000, 9999)}",
        'ip': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        'status': status
    }
    
    return transaction


def main():
    """Main producer loop"""
    logger.info(f"Starting producer - connecting to {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Target date: {DEFAULT_DATE}")
    logger.info(f"Batch size: {TRANSACTIONS_PER_BATCH}, Interval: {BATCH_INTERVAL_SECONDS}s")
    
    # Initialize Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3
    )
    
    logger.info(f"Connected to Kafka, producing to topic: {KAFKA_TOPIC}")
    
    batch_count = 0
    total_sent = 0
    
    try:
        while True:
            batch_count += 1
            logger.info(f"Generating batch {batch_count}...")
            
            for _ in range(TRANSACTIONS_PER_BATCH):
                transaction = generate_transaction(target_date=DEFAULT_DATE)
                
                # Send to Kafka
                future = producer.send(KAFKA_TOPIC, value=transaction)
                future.get(timeout=10)  # Wait for confirmation
                total_sent += 1
            
            producer.flush()
            logger.info(f"Batch {batch_count} sent ({TRANSACTIONS_PER_BATCH} transactions). Total: {total_sent}")
            
            # Wait before next batch
            sleep(BATCH_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        logger.info("Producer stopped by user")
    except Exception as e:
        logger.error(f"Error in producer: {e}", exc_info=True)
    finally:
        producer.close()
        logger.info(f"Producer closed. Total transactions sent: {total_sent}")


if __name__ == '__main__':
    main()
