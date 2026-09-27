#!/usr/bin/env python3
"""Apply ch07 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch07-performance.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 intro
("""The concepts here apply to both PostgreSQL and SQL Server, though the mechanics differ meaningfully between them, and those differences matter when you are under pressure to solve a problem fast.""",
 """The mechanics here are SQL Server's throughout — and those mechanics are what matter when you are under pressure to solve a problem fast."""),

# 2 optimizer
("""PostgreSQL uses a cost-based optimizer that considers sequential scans, index scans, bitmap index scans, hash joins, merge joins, nested loops, and more. It uses statistics stored in %s and exposed through %s. SQL Server's optimizer is also cost-based and relies on statistics objects stored in %s, with column-level density and histograms that guide join strategies and seek-versus-scan decisions.""" % (code('pg_statistic'), code('pg_stats'), code('sys.stats')),
 """SQL Server uses a cost-based optimizer that considers index seeks and scans, nested loops, hash joins, and merge joins. It relies on statistics objects stored in %s, with column-level density and multi-step histograms that guide join strategies and seek-versus-scan decisions.""" % code('sys.stats')),

# 3 EXPLAIN -> plans
("""In PostgreSQL, you generate a plan using %s for the estimated plan or %s for the actual execution with runtime statistics. %s runs the query, so avoid it on expensive writes unless you wrap them in a transaction you can roll back.""" % (code('EXPLAIN'), code('EXPLAIN ANALYZE'), code('EXPLAIN ANALYZE')),
 """In SQL Server, you generate a plan as an estimated execution plan (Ctrl+L in SSMS) or an actual execution plan that includes runtime statistics. Capturing an actual plan executes the query, so avoid it on expensive writes in production unless you can tolerate the side effects — use a transaction you can roll back, or a restored copy of the database."""),

# 4 reading plans
("""When reading a PostgreSQL %s output, the most important things to look for are the difference between estimated rows and actual rows, the nodes where most time is spent, and whether the planner chose an appropriate join type. A node showing %s estimated but %s actual is a red flag — the optimizer is flying blind, and that typically means statistics need updating or a histogram bucket is too coarse for your data distribution.""" % (code('EXPLAIN ANALYZE'), code('rows=1'), code('rows=847523')),
 """When reading an actual execution plan, the most important things to look for are the difference between estimated and actual row counts, the operators where most time is spent, and whether the optimizer chose an appropriate join type. An operator showing 1 estimated row but 847,523 actual rows is a red flag — the optimizer is flying blind, and that typically means statistics need updating or a histogram step is too coarse for your data distribution."""),

# 5 key metrics
("""whether hash joins are spilling to disk (indicated by "Hash Batches > 1" in PostgreSQL and a yellow warning icon in SQL Server), whether sorts are hitting memory limits,""",
 """whether hash joins or sorts are spilling to tempdb (indicated by a yellow warning icon on the operator), whether memory grants are being throttled,"""),

# 6 statistics maintenance
("""PostgreSQL maintains statistics through %s, which samples tables and updates the histograms and most-common-value lists stored in %s. The %s daemon runs %s automatically based on configurable thresholds, but in high-write environments, statistics can lag significantly behind reality. For a table with tens of millions of rows being inserted into at high volume, autovacuum's default trigger (20%% of rows changed) may not fire often enough.""" % (code('ANALYZE'), code('pg_statistic'), code('autovacuum'), code('ANALYZE')),
 """SQL Server maintains statistics through auto-update statistics, which samples tables and refreshes histograms when roughly 20%% of rows change — but in high-write environments, statistics can lag significantly behind reality. For a table with tens of millions of rows being inserted at high volume, the default trigger may not fire often enough; trace flag 2371 (behavior default since SQL Server 2016) lowers the threshold dynamically for large tables. For very large or skewed tables, %s with FULLSCAN on a schedule — or filtered statistics on hot partitions — beats relying on auto-update.""" % code('UPDATE STATISTICS')),

# 7 parameter sniffing
("""One of the most insidious cardinality problems in both databases is parameter sniffing.""",
 """One of the most insidious cardinality problems in SQL Server is parameter sniffing."""),
("""In PostgreSQL, this manifests in PL/pgSQL functions where the plan is cached after first execution. In SQL Server, it is an extremely common production issue with stored procedures. The solutions involve query plan recompilation, %s hints in SQL Server, or restructuring the query to avoid plan sensitivity.""" % code('OPTION (RECOMPILE)'),
 """In SQL Server, it is an extremely common production issue with stored procedures. The solutions include %s hints, %s for unknown-at-compile-time values, plan guides, or forcing a known-good plan through Query Store — or restructuring the query to avoid plan sensitivity in the first place.""" % (code('OPTION (RECOMPILE)'), code('OPTIMIZE FOR UNKNOWN'))),

# 8 workload analysis intro
("""Both PostgreSQL and SQL Server expose rich system views and dynamic management views that let you identify the worst offenders across the entire workload without having to examine every query one by one.""",
 """SQL Server exposes rich dynamic management views that let you identify the worst offenders across the entire workload without having to examine every query one by one."""),

# 9 pg_stat_statements -> dm_exec_query_stats
("""PostgreSQL's %s extension is the starting point for workload analysis. Once enabled, it tracks query execution across all connections, aggregating statistics by normalized query text. You can sort by total time, mean time, or I/O reads to find exactly where your database is spending its time.""" % code('pg_stat_statements'),
 """%s is the starting point for workload analysis. It tracks query execution across all connections, aggregating statistics by query hash and plan handle. You can sort by total worker time, total elapsed time, or logical reads to find exactly where your database is spending its time. Combined with %s and %s, it gives you the text and the plan behind every offending query.""" % (code('sys.dm_exec_query_stats'), code('sys.dm_exec_sql_text'), code('sys.dm_exec_query_plan'))),

# 10 blocking
("""PostgreSQL surfaces active query information through %s. For lock contention analysis, joining %s with %s reveals which backends are holding locks that others are waiting for. This is the PostgreSQL equivalent of SQL Server's blocking chain analysis, and in high-concurrency environments, unresolved lock chains can cascade into full-scale connection exhaustion.""" % (code('pg_stat_activity'), code('pg_stat_activity'), code('pg_locks')),
 """SQL Server surfaces active request information through %s. For lock contention analysis, joining %s with %s reveals which sessions are holding locks that others are waiting for — the classic blocking-chain analysis. In high-concurrency environments, unresolved blocking chains can cascade into worker-thread exhaustion.""" % (code('sys.dm_exec_requests'), code('sys.dm_exec_requests'), code('sys.dm_os_waiting_tasks'))),

# 11 object-level stats
("""PostgreSQL's %s shows heap fetches, sequential scans, index scans, live and dead tuples, and when the table was last vacuumed and analyzed. A table with a very high ratio of sequential scans to index scans on a large dataset usually indicates a missing or underutilized index. SQL Server's %s provides similar insight — how many seeks, scans, and lookups an index has served, and how many rows have been inserted, updated, or deleted through it. An index that has zero seeks and thousands of updates is costing you write overhead without providing read benefit, and it is a candidate for removal.""" % (code('pg_stat_user_tables'), code('sys.dm_db_index_usage_stats')),
 """SQL Server's %s provides object-level insight — how many seeks, scans, and lookups an index has served, and how many rows have been inserted, updated, or deleted through it. A large table with a very high ratio of scans to seeks usually indicates a missing or underutilized index. An index that has zero seeks and thousands of updates is costing you write overhead without providing read benefit, and it is a candidate for removal.""" % code('sys.dm_db_index_usage_stats')),

# 12 functional index
("""or to create a functional index (PostgreSQL) or a computed column with an index (SQL Server) that pre-computes the expression.""",
 """or to create a computed column with an index that pre-computes the expression."""),

# 13 implicit conversions
("""PostgreSQL handles some implicit conversions more gracefully, but the general principle holds: matching data types between columns and their filter values is not just good practice, it is a prerequisite for efficient execution.""",
 """Matching data types between columns and their filter values is not just good practice, it is a prerequisite for efficient execution — check the plan for CONVERT_IMPLICIT warnings on seek predicates."""),

# 14 CTEs
("""CTEs present a subtle optimization trap in PostgreSQL. Prior to PostgreSQL 12, all CTEs were optimization fences — the planner would materialize the CTE result into a temporary structure and prevent itself from pushing filter predicates down into the CTE. This meant that even if your outer query filtered heavily, the CTE would process all its rows first. Since PostgreSQL 12, the planner inlines CTEs by default when they are referenced only once and not recursive, but older codebases running on earlier versions still carry this problem. In SQL Server, CTEs are never materialized by default; they are expanded inline before optimization, so they do not carry this risk.""",
 """CTEs in SQL Server are expanded inline before optimization — they are never materialized by default, so they carry no optimization-fence risk. The subtler trap is recursive CTEs and deeply nested CTE chains that make plans hard to read and can hide cardinality misestimates; when a CTE-based query misbehaves, check whether the optimizer's row estimates collapse at the CTE boundary, and consider materializing complex multi-step logic into a temp table yourself so each step gets its own statistics and plan."""),

# 15 partitioning
("""Both PostgreSQL (declarative partitioning since version 10) and SQL Server (partition functions and schemes) support this pattern. The key insight is that partition pruning only works when the filter condition is on the partition key column and the value is known at planning time — a filter like %s may not prune correctly if the planner cannot resolve the expression statically.""" % code('WHERE year_col = EXTRACT(YEAR FROM NOW())'),
 """SQL Server supports this pattern through partition functions and schemes. The key insight is that partition elimination only works when the filter condition is on the partition key column and the value is known at optimization time — a filter like %s may not eliminate partitions if the optimizer cannot resolve the expression statically, so prefer sargable range predicates directly on the partition key.""" % code('WHERE YEAR(order_date) = YEAR(GETDATE())')),

# 16 memory -> grants
("""In PostgreSQL, %s controls how much memory each sort or hash operation can use before spilling to disk. The default is 4MB, which is deliberately conservative because the value applies per operation per connection — a complex query with multiple sort nodes, run by 100 concurrent connections, could consume %s memory simultaneously. In practice, a %s of 4MB forces many sorts and hash joins on large datasets to spill to disk, causing dramatic slowdowns. The right approach is to leave the global %s at a safe value for OLTP workloads and use %s at the session level for known analytical queries or batch jobs that need it. Similarly, %s should be set to roughly 25%% of total RAM for a dedicated PostgreSQL server, with the operating system page cache handling the rest. The %s parameter does not allocate memory — it tells the planner how much memory it can assume is available for caching, affecting whether the planner prefers index scans over sequential scans.""" % (code('work_mem'), code('work_mem * sort_nodes * 100'), code('work_mem'), code('work_mem'), code("SET work_mem = '256MB'"), code('shared_buffers'), code('effective_cache_size')),
 """In SQL Server, the memory available for sorts and hash operations comes from <strong class="text-white">memory grants</strong>, drawn from the buffer pool's workspace memory. A query that needs more memory than its grant gets spills to tempdb — watch for the sort and hash warnings in Extended Events. The server-level max memory setting caps the buffer pool; the standard guidance is to leave 4GB or 10%% of RAM (whichever is larger) for the OS, and more on servers running other services. Memory grants are per-query, and Resource Governor workload groups let you cap how much memory analytical sessions can consume — so a single runaway report cannot starve the OLTP workload of grant memory. When spills are chronic, the fix is rarely "more memory": it is usually stale statistics producing a tiny grant estimate, or a missing index forcing a sort the plan shouldn't need."""),

# 17 parallelism PG -> cost threshold/MAXDOP
("""Parallel query execution is a double-edged tool. Both databases can split a single query across multiple CPU cores, which speeds up large analytical queries but can harm OLTP throughput when too many parallel workers compete for CPU. In PostgreSQL, %s controls how many workers a single query node can use, and %s and %s influence when the planner decides parallelism is worth the overhead. For OLTP workloads with many small, fast queries, parallelism often adds more latency than it removes — the setup cost of spawning workers exceeds the benefit on a query that runs in 2ms. For analytical workloads doing full-table aggregations, parallelism is frequently the difference between a 45-second query and a 6-second one.""" % (code('max_parallel_workers_per_gather'), code('parallel_tuple_cost'), code('parallel_setup_cost')),
 """Parallel query execution is a double-edged tool. SQL Server can split a single query across multiple schedulers when the estimated cost exceeds the cost threshold for parallelism and MAXDOP allows it — which speeds up large analytical queries but can harm OLTP throughput when too many parallel workers compete for CPU. For OLTP workloads with many small, fast queries, parallelism often adds more latency than it removes: the exchange-operator overhead exceeds the benefit on a query that runs in 2ms. The modern guidance is to raise cost threshold for parallelism from the ancient default of 5 to the 25–50 range, and set MAXDOP per workload (often 4–8 for OLTP, higher for dedicated analytics). For analytical workloads doing full-table aggregations, parallelism is frequently the difference between a 45-second query and a 6-second one."""),

# 18 resource governor PG tail
("""PostgreSQL has no built-in equivalent; DBAs typically approximate the same effect by routing analytical connections through a separate connection pool with a role-level %s and %s setting, or by directing heavy reporting queries to a read replica entirely, so a single expensive report cannot consume resources that OLTP transactions need.""" % (code('statement_timeout'), code('work_mem')),
 """For finer control, Resource Governor workload groups can cap CPU and memory per session classification, and readable secondaries let you direct heavy reporting queries to a replica entirely — so a single expensive report cannot consume resources that OLTP transactions need."""),

# 19 index maintenance PG tail
(""" In PostgreSQL, fragmentation manifests as dead tuple bloat rather than page-level fragmentation, and %s is the tool that reclaims dead tuple space. Unlike SQL Server's index rebuild, %s does not reorder data pages, which means that for very bloated tables, a %s (which rewrites the entire table) or %s (a third-party extension that rewrites online) may be needed — but both approaches require careful planning because %s takes an exclusive lock while %s does not.""" % (code('VACUUM'), code('VACUUM'), code('VACUUM FULL'), code('pg_repack'), code('VACUUM FULL'), code('pg_repack')),
 """ Ola Hallengren's IndexOptimize remains the community-standard implementation of this policy — it encodes the rebuild-vs-reorganize decision, online options, and statistics updates as one maintained solution rather than hand-rolled Agent jobs."""),

# 20 takeaway plans
("""`EXPLAIN ANALYZE` in PostgreSQL and actual execution plans in SQL Server tell you exactly where time and I/O are going — no other signal is more reliable for query-level diagnosis.""",
 """Actual execution plans in SQL Server tell you exactly where time and I/O are going — no other signal is more reliable for query-level diagnosis."""),

# 21 takeaway workload
("""`pg_stat_statements` and `sys.dm_exec_query_stats` let you identify the highest-impact queries across the entire instance, so you optimize what actually matters rather than what is easiest to find.""",
 """`sys.dm_exec_query_stats` and Query Store let you identify the highest-impact queries across the entire instance, so you optimize what actually matters rather than what is easiest to find."""),
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
    print(f'ch07: all {len(REPLACEMENTS)} replacements applied')

main()
