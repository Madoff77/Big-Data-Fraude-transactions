#!/usr/bin/env python3
"""
MR2 Reducer: merchant_daily_metrics
Aggregates transactions by (dt, merchant_id)
Computes: tx_count, sum_amount, avg_amount, max_amount, unique_countries, unique_devices, decline_rate
"""
import sys
from collections import defaultdict


def main():
    """Read grouped data from stdin, compute aggregates"""
    current_key = None
    tx_count = 0
    sum_amount = 0.0
    max_amount = 0.0
    countries = set()
    devices = set()
    declined_count = 0
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) < 6:
            continue
        
        # Parse: dt, merchant_id, amount, country, device_id, status
        dt = parts[0]
        merchant_id = parts[1]
        amount = float(parts[2])
        country = parts[3]
        device_id = parts[4]
        status = parts[5]
        
        key = f"{dt}\t{merchant_id}"
        
        # New key - emit previous and reset
        if current_key and current_key != key:
            emit_metrics(current_key, tx_count, sum_amount, max_amount, 
                        countries, devices, declined_count)
            
            # Reset accumulators
            tx_count = 0
            sum_amount = 0.0
            max_amount = 0.0
            countries = set()
            devices = set()
            declined_count = 0
        
        # Accumulate
        current_key = key
        tx_count += 1
        sum_amount += amount
        max_amount = max(max_amount, amount)
        countries.add(country)
        devices.add(device_id)
        if status == 'DECLINED':
            declined_count += 1
    
    # Emit last group
    if current_key:
        emit_metrics(current_key, tx_count, sum_amount, max_amount, 
                    countries, devices, declined_count)


def emit_metrics(key, tx_count, sum_amount, max_amount, countries, devices, declined_count):
    """Emit aggregated metrics as TSV"""
    dt, merchant_id = key.split('\t')
    
    avg_amount = sum_amount / tx_count if tx_count > 0 else 0.0
    unique_countries = len(countries)
    unique_devices = len(devices)
    decline_rate = declined_count / tx_count if tx_count > 0 else 0.0
    
    # Output: dt, merchant_id, tx_count, sum_amount, avg_amount, max_amount, unique_countries, unique_devices, decline_rate
    output = "\t".join([
        dt,
        merchant_id,
        str(tx_count),
        f"{sum_amount:.2f}",
        f"{avg_amount:.2f}",
        f"{max_amount:.2f}",
        str(unique_countries),
        str(unique_devices),
        f"{decline_rate:.4f}"
    ])
    print(output)


if __name__ == '__main__':
    main()
