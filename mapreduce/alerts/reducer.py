#!/usr/bin/env python3
"""
MR3 Reducer: alerts_generation
Identity reducer - just pass through alerts
"""
import sys


def main():
    """Read JSONL alerts from stdin, write to stdout"""
    for line in sys.stdin:
        line = line.strip()
        if line:
            print(line)


if __name__ == '__main__':
    main()
