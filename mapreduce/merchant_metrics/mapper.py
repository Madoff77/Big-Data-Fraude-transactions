#!/usr/bin/env python3
"""
MR2 Mapper: merchant_daily_metrics
Reads clean TSV, emits key-value for aggregation
Key: dt \t merchant_id
Value: amount \t country \t device_id \t status
"""
import sys


def main():
    """Read clean TSV from stdin, emit key-value pairs"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) < 13:
            continue
        
        # Parse fields
        # tx_id, ts, dt, hour, customer_id, merchant_id, country, amount, currency, payment_method, device_id, ip, status
        dt = parts[2]
        merchant_id = parts[5]
        country = parts[6]
        amount = parts[7]
        device_id = parts[10]
        status = parts[12]
        
        # Emit: key = (dt, merchant_id), value = (amount, country, device_id, status)
        key = f"{dt}\t{merchant_id}"
        value = f"{amount}\t{country}\t{device_id}\t{status}"
        
        print(f"{key}\t{value}")


if __name__ == '__main__':
    main()
