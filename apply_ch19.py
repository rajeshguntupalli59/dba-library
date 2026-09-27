#!/usr/bin/env python3
"""Apply ch19 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch19-testing.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 test copies
("""For PostgreSQL, %s and %s are the standard tools for creating a schema-level copy. For a data subset, you can dump specific tables with row filtering. For SQL Server, database backups with restore, or database snapshots, are the typical approach.""" % (code('pg_dump'), code('pg_restore')),
 """For SQL Server, the typical approaches for creating a test copy are restoring a backup with a new name (%s), database snapshots, or BACPAC exports. For a data subset, restore the full backup and delete down, or extract the slice with SSIS/ADF — the key is that the test copy's schema and statistics match production, or your test results won't transfer.""" % code('WITH MOVE')),

# 2 masking
("""PostgreSQL's %s extension and SQL Server's built-in %s or dynamic data masking features both support this.""" % (code('pgcrypto'), code('HASHBYTES')),
 """SQL Server's built-in %s, dynamic data masking, or Always Encrypted support this.""" % code('HASHBYTES')),

# 3 config parity
("""If your production PostgreSQL server runs with %s and %s, your test environment should match those settings when you're evaluating query plans. A hash join that's chosen in production but blocked by lower %s in staging will make your test results meaningless.""" % (code('work_mem = 64MB'), code('enable_hashjoin = on'), code('work_mem')),
 """If your production server runs with a non-default %s or %s, your test environment should match those settings when you're evaluating query plans. A parallel plan chosen in production but blocked by %s in staging will make your test results meaningless.""" % (code('cost threshold for parallelism'), code('MAXDOP'), code('MAXDOP = 1'))),

# 4 migration locks
("""cause lock contention (adding a column with a default value in older PostgreSQL versions), or break application queries (renaming a column that wasn't fully searched in the codebase).""",
 """cause lock contention (adding a NOT NULL column with a default to a huge table without online options), or break application queries (renaming a column that wasn't fully searched in the codebase)."""),

# 5 FK validation
("""In PostgreSQL, adding a foreign key constraint with large tables can create an index entry in %s with %s if you used %s during creation — meaning the constraint was added but hasn't been checked against existing rows yet. You need to explicitly run %s afterward, and you should verify this in your post-migration checks.""" % (code('pg_constraint'), code('convalidated = false'), code('NOT VALID'), code('VALIDATE CONSTRAINT')),
 """In SQL Server, adding a foreign key to a large table validates existing rows by default — use %s to add it quickly as untrusted, then validate later with %s. An untrusted constraint is ignored by the optimizer, so verify trust status in %s (%s) in your post-migration checks.""" % (code('WITH NOCHECK'), code('WITH CHECK CHECK CONSTRAINT'), code('sys.foreign_keys'), code('is_not_trusted = 1'))),

# 6 EXCEPT/MINUS
("""For row-level differential queries, use an %s or %s based approach (PostgreSQL supports %s; SQL Server supports %s as well).""" % (code('EXCEPT'), code('MINUS'), code('EXCEPT'), code('EXCEPT')),
 """For row-level differential queries, use an %s-based approach (SQL Server supports %s).""" % (code('EXCEPT'), code('EXCEPT'))),

# 7 top queries source
("""You can identify these from %s in PostgreSQL or from the Query Store in SQL Server.""" % code('pg_stat_statements'),
 """You can identify these from Query Store — sort by total duration or CPU over your baseline window."""),

# 8 auto_explain
("""For PostgreSQL, %s is a valuable extension for capturing plans of slow queries automatically during a test run without manually running each one. Load it as a shared library, set %s (in milliseconds), and run your workload. Plans for all queries exceeding the threshold are written to the PostgreSQL log.""" % (code('auto_explain'), code('auto_explain.log_min_duration = 100')),
 """For automatic plan capture during a test run, Query Store is already recording plans and wait stats on the test database — run your workload, then compare top-resource queries before and after. For ad-hoc capture, an Extended Events session on %s with a duration predicate logs every slow query's text and plan handle without manual effort.""" % code('sql_batch_completed')),

# 9 statistics
("""When you load a large dataset, run %s (PostgreSQL) or %s (SQL Server), and then test queries,""" % (code('ANALYZE'), code('UPDATE STATISTICS')),
 """When you load a large dataset, run %s, and then test queries,""" % code('UPDATE STATISTICS')),

# 10 concurrency effects
("""Lock contention, buffer pool competition, connection overhead, and autovacuum interference are all concurrency effects that only appear under load.""",
 """Lock contention, buffer pool competition, connection overhead, and tempdb contention are all concurrency effects that only appear under load."""),

# 11 pgbench
("""For PostgreSQL, %s is the built-in load testing tool. It ships with a standard TPC-B-like workload, but its real value is that it accepts custom SQL scripts so you can drive it with your actual application queries. A typical pre-deployment validation run uses a custom script containing the top five write paths in the application, run at 50 concurrent clients for ten minutes, and measures transactions per second and average latency.""" % code('pgbench'),
 """For SQL Server, the workhorse load-testing tools are %s (from the RML utilities) and HammerDB. ostress replays a T-SQL script at N concurrent connections and reports throughput and latency — ideal for pre-deployment validation: a custom script with the top five write paths, 50 concurrent connections for ten minutes, measuring batches per second and average latency. Distributed Replay handles full production-trace replay when you need fidelity to the real workload mix.""" % code('ostress')),

# 12 autovacuum under load
("""One specific thing to watch in PostgreSQL during load tests is autovacuum activity. Autovacuum is triggered by write load, so a load test that drives a high INSERT/UPDATE rate will also trigger autovacuum on the affected tables. If autovacuum can't keep up, table bloat increases and query plans may degrade. Monitor %s for %s growing during your load test — a sign that autovacuum is falling behind.""" % (code('pg_stat_user_tables'), code('n_dead_tup')),
 """One specific thing to watch during load tests is tempdb contention: version-store growth under RCSI, allocation-page latch contention (PFS/GAM/SGAM), and sort/hash spills all surface under concurrent load. Monitor %s and wait stats for %s waits on tempdb pages — a sign your load test is bottlenecked on tempdb rather than the workload itself.""" % (code('sys.dm_db_file_space_usage'), code('PAGELATCH_UP'))),

# 13 takeaway regression
("""Capture execution plans and timing from `pg_stat_statements` or SQL Server Query Store for your critical queries, and compare them explicitly rather than assuming the planner will make the same choices.""",
 """Capture execution plans and timing from Query Store for your critical queries, and compare them explicitly rather than assuming the optimizer will make the same choices."""),

# 14 takeaway load testing
("""lock contention, autovacuum lag, P99 latency spikes, and connection pool exhaustion are all concurrency effects.""",
 """lock contention, tempdb pressure, P99 latency spikes, and connection pool exhaustion are all concurrency effects."""),
]

def main():
    text = open(PATH).read()
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch19: all {len(REPLACEMENTS)} replacements applied')

main()
