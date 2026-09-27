#!/usr/bin/env python3
"""Verify a rewritten chapter: PG terms gone, word count, tag balance, chapter header.
Usage: python3 verify_ch.py book/ch03-architecture.html 3"""
import re, sys

PG = re.compile(
    r'postgres|pg_stat|pg_catalog|pg_\w+|'
    r'\bWAL\b|\bwal\b|wal_\w+|\bpsql\b|autovacuum|\bvacuum\b|'
    r'Patroni|PgBouncer|pgpool|Citus|pglogical|synchronous_standby|'
    r'max_connections|pg_hba|\bTOAST\b|\bXID\b|hot_standby',
    re.IGNORECASE,
)

path, num = sys.argv[1], sys.argv[2]
t = open(path).read()

# PG terms (show matches with context)
bad = []
for m in PG.finditer(t):
    s = max(0, m.start() - 40); e = min(len(t), m.end() + 40)
    bad.append(t[s:e].replace('\n', ' '))
if bad:
    print(f'PG TERMS REMAINING: {len(bad)}')
    for b in bad[:15]:
        print('  ...' + b + '...')
else:
    print('PG terms: clean')

# word count (prose only)
text = re.sub(r'<script.*?</script>', '', t, flags=re.S)
text = re.sub(r'<style.*?</style>', '', text, flags=re.S)
text = re.sub(r'<[^>]+>', ' ', text)
words = len([w for w in text.split() if w.strip()])
print(f'words: {words} ({">1200 OK" if words > 1200 else "TOO SHORT"})')

# tag balance
for tag in ['p', 'li', 'h2', 'h3', 'h4', 'pre', 'code', 'div', 'ul', 'ol', 'table', 'article', 'span', 'a', 'strong', 'em']:
    o = len(re.findall(r'<%s[ >]' % tag, t)); c = t.count('</%s>' % tag)
    if o != c:
        print(f'IMBALANCE {tag}: open={o} close={c}')

# chapter header
m = re.search(r'Chapter (\d+) of (\d+)', t)
print('header:', m.group(0) if m else 'MISSING')
if m and (m.group(1) != num or m.group(2) != '40'):
    print(f'HEADER MISMATCH: expected Chapter {num} of 40')
print('verify done')
