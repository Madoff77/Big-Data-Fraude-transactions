#!/usr/bin/env python3
"""
MR1 Mapper: clean_normalize
Reads JSONL from stdin, validates, normalizes, outputs TSV
"""
import sys
import json
from datetime import datetime


def parse_and_validate(line):
    """Parse JSON and validate required fields"""
    try:
        txn = json.loads(line.strip())
        
        # Required fields
        required = ['tx_id', 'ts', 'customer_id', 'merchant_id', 'country', 
                   'amount', 'currency', 'payment_method', 'device_id', 'ip', 'status']
        
        for field in required:
            if field not in txn:
                return None, f"Missing field: {field}"
        
        # Validate and normalize types
        try:
            amount = float(txn['amount'])
            if amount < 0:
                return None, "Negative amount"
        except (ValueError, TypeError):
            return None, "Invalid amount"
        
        # Validate timestamp format
        try:
            ts = datetime.fromisoformat(txn['ts'].replace('Z', '+00:00'))
        except:
            return None, "Invalid timestamp"
        
        # Extract date and hour for partitioning
        dt = ts.strftime('%Y-%m-%d')
        hour = ts.strftime('%H')
        
        # Validate status
        status = txn['status'].upper()
        if status not in ['APPROVED', 'DECLINED']:
            return None, "Invalid status"
        
        # Build clean record
        clean = {
            'tx_id': str(txn['tx_id']).strip(),
            'ts': txn['ts'],
            'dt': dt,
            'hour': hour,
            'customer_id': str(txn['customer_id']).strip(),
            'merchant_id': str(txn['merchant_id']).strip(),
            'country': str(txn['country']).strip().upper(),
            'amount': amount,
            'currency': str(txn['currency']).strip().upper(),
            'payment_method': str(txn['payment_method']).strip().upper(),
            'device_id': str(txn['device_id']).strip(),
            'ip': str(txn['ip']).strip(),
            'status': status
        }
        
        return clean, None
        
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def main():
    """Read from stdin, parse, validate, emit clean TSV to stdout"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        clean, error = parse_and_validate(line)
        
        if error:
            # Log errors to stderr
            print(f"VALIDATION_ERROR\t{error}", file=sys.stderr)
            continue
        
        # Emit clean record as TSV
        # Format: tx_id \t ts \t dt \t hour \t customer_id \t merchant_id \t country \t amount \t currency \t payment_method \t device_id \t ip \t status
        output = "\t".join([
            clean['tx_id'],
            clean['ts'],
            clean['dt'],
            clean['hour'],
            clean['customer_id'],
            clean['merchant_id'],
            clean['country'],
            str(clean['amount']),
            clean['currency'],
            clean['payment_method'],
            clean['device_id'],
            clean['ip'],
            clean['status']
        ])
        print(output)


if __name__ == '__main__':
    main()
