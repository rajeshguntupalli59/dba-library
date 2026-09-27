#!/usr/bin/env python3
"""Extract blocks containing PostgreSQL references from chapter HTML files.
Usage: python3 extract_pg.py ch01-introduction.html [ch02-...]
Prints numbered blocks with line ranges for rewriting."""
import re, sys, html

PG = re.compile(
    r'postgres|pg_stat|pg_catalog|pg_\w+|pgcrypto|'
    r'\bWAL\b|\bwal\b|wal_\w+|\bpsql\b|autovacuum|\bVACUUM\b|\bvacuum\b|'
    r'Patroni|PgBouncer|pgpool|Citus|pglogical|synchronous_standby|'
    r'max_connections|pg_hba|TOAST\b|\bXID\b|hot_standby|'
    r'both platforms|two platforms|side by side|the other platform|'
    r'each platform|either platform',
    re.IGNORECASE,
)

def blocks_of(text):
    """Yield (start_line, end_line, block_text) for p/li/h2/h3/h4/pre/table blocks."""
    lines = text.split('\n')
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        # multi-line pre block
        if '<pre' in line:
            j = i
            while j < n and '</pre>' not in lines[j]:
                j += 1
            yield (i + 1, j + 1, '\n'.join(lines[i:j + 1]))
            i = j + 1
            continue
        # single-line content blocks
        if re.search(r'<(p|li|h2|h3|h4|td|th|tr|div)\b', line):
            yield (i + 1, i + 1, line)
        i += 1

def main():
    for path in sys.argv[1:]:
        text = open(path).read()
        found = 0
        for (sl, el, blk) in blocks_of(text):
            # strip tags for matching but show raw
            if PG.search(blk):
                found += 1
                print(f'--- {path} :: BLOCK {found} :: lines {sl}-{el} ---')
                print(blk)
                print()
        if found == 0:
            print(f'--- {path}: no PG blocks found ---')

if __name__ == '__main__':
    main()
