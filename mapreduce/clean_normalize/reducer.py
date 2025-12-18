#!/usr/bin/env python3
"""
MR1 Reducer: clean_normalize
Simply passes through the clean records (identity reducer)
"""
import sys


def main():
    """Read TSV from stdin, write to stdout"""
    for line in sys.stdin:
        line = line.strip()
        if line:
            print(line)


if __name__ == '__main__':
    main()
