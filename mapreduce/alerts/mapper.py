#!/usr/bin/env python3
"""
MR3 Mapper: alerts_generation
Reads merchant metrics TSV, applies rules, emits alerts
This is a map-only job (no reducer needed, or identity reducer)
"""
import sys
import json
import uuid


# Alert rules
RULES = {
    'HIGH_AMOUNT': {'threshold': 1000, 'field': 'max_amount', 'severity': 3},
    'BURST': {'threshold': 30, 'field': 'tx_count', 'severity': 2},
    'MULTI_COUNTRY': {'threshold': 3, 'field': 'unique_countries', 'severity': 2},
    'HIGH_DECLINE': {'threshold': 0.5, 'field': 'decline_rate', 'severity': 3}
}


def check_rules(metrics):
    """Check all rules and return list of triggered alerts"""
    alerts = []
    
    for rule_code, rule_config in RULES.items():
        field = rule_config['field']
        threshold = rule_config['threshold']
        severity = rule_config['severity']
        
        value = metrics.get(field, 0)
        
        if rule_code == 'HIGH_AMOUNT' and value > threshold:
            alerts.append({
                'alert_id': str(uuid.uuid4()),
                'dt': metrics['dt'],
                'merchant_id': metrics['merchant_id'],
                'customer_id': None,
                'rule_code': rule_code,
                'severity': severity,
                'details': {
                    'max_amount': value,
                    'threshold': threshold
                }
            })
        elif rule_code == 'BURST' and value > threshold:
            alerts.append({
                'alert_id': str(uuid.uuid4()),
                'dt': metrics['dt'],
                'merchant_id': metrics['merchant_id'],
                'customer_id': None,
                'rule_code': rule_code,
                'severity': severity,
                'details': {
                    'tx_count': value,
                    'threshold': threshold
                }
            })
        elif rule_code == 'MULTI_COUNTRY' and value >= threshold:
            alerts.append({
                'alert_id': str(uuid.uuid4()),
                'dt': metrics['dt'],
                'merchant_id': metrics['merchant_id'],
                'customer_id': None,
                'rule_code': rule_code,
                'severity': severity,
                'details': {
                    'unique_countries': value,
                    'threshold': threshold
                }
            })
        elif rule_code == 'HIGH_DECLINE' and value > threshold:
            alerts.append({
                'alert_id': str(uuid.uuid4()),
                'dt': metrics['dt'],
                'merchant_id': metrics['merchant_id'],
                'customer_id': None,
                'rule_code': rule_code,
                'severity': severity,
                'details': {
                    'decline_rate': value,
                    'threshold': threshold
                }
            })
    
    return alerts


def main():
    """Read merchant metrics from stdin, apply rules, emit alerts as JSONL"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) < 9:
            continue
        
        # Parse: dt, merchant_id, tx_count, sum_amount, avg_amount, max_amount, unique_countries, unique_devices, decline_rate
        metrics = {
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
        
        # Check rules
        alerts = check_rules(metrics)
        
        # Emit alerts as JSONL
        for alert in alerts:
            print(json.dumps(alert))


if __name__ == '__main__':
    main()
