#!/usr/bin/env python3
"""Apply ch32 phrase-level rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch32-observability.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
("the tools and techniques that modern PostgreSQL and SQL Server offer for deep observability,",
 "the tools and techniques that modern SQL Server offers for deep observability,"),
("slow queries, errors, autovacuum runs, checkpoint completions.",
 "slow queries, errors, index maintenance runs, checkpoint completions."),
("""Both PostgreSQL and SQL Server have matured significantly in this space. PostgreSQL ships with the %s family of catalog views, the %s extension, and the %s module. SQL Server provides Dynamic Management Views (DMVs), Extended Events, Query Store, and Wait Statistics.""" % (code('pg_stat_*'), code('pg_stat_statements'), code('auto_explain')),
 """SQL Server has matured significantly in this space. It provides Dynamic Management Views (DMVs), Extended Events, Query Store, and Wait Statistics — a complete observability stack built into the engine."""),
("The Statistics Infrastructure: pg_stat_* and SQL Server DMVs",
 "The Statistics Infrastructure: SQL Server DMVs"),
("**PostgreSQL's pg_stat_* Views**",
 "**SQL Server's DMV Families**"),
("PostgreSQL maintains a family of cumulative statistics views that the statistics collector process updates asynchronously. The most useful ones for day-to-day work are:",
 "SQL Server exposes hundreds of DMVs grouped by functional area. The most useful ones for day-to-day work are:"),
("`pg_stat_activity` — currently running sessions and their states",
 "`sys.dm_exec_requests` + `sys.dm_exec_sessions` — currently running sessions and their states"),
("`pg_stat_statements` — aggregated execution stats per normalized query",
 "`sys.dm_exec_query_stats` — aggregated execution stats per cached plan"),
("`pg_stat_bgwriter` — checkpoint and background writer activity",
 "`sys.dm_os_wait_stats` — cumulative wait statistics by wait type"),
("`pg_stat_user_tables` — heap fetches, index scans, live/dead tuples per table",
 "`sys.dm_db_index_usage_stats` — seeks, scans, lookups, and writes per index"),
("`pg_stat_user_indexes` — scans and tuples read per index",
 "`sys.dm_db_missing_index_details` — indexes the optimizer wishes existed"),
("`pg_statio_user_tables` — buffer hits vs disk reads at the table level",
 "`sys.dm_io_virtual_file_stats` — read/write latency per database file"),
("The %s view is where you start whenever something is running slow right now:" % code('pg_stat_activity'),
 "The %s view is where you start whenever something is running slow right now:" % code('sys.dm_exec_requests')),
("""SQL Server's Dynamic Management Views and Functions (DMVs/DMFs) are the rough equivalent of PostgreSQL's %s views, but they are much more granular and cover areas PostgreSQL does not expose directly at the view level — things like index usage statistics, missing index hints, and memory grant information.""" % code('pg_stat_*'),
 """SQL Server's Dynamic Management Views and Functions (DMVs/DMFs) are far more granular than a single statistics view — they expose index usage statistics, missing index hints, and memory grant information directly at the view level."""),
("PostgreSQL's statistics reset with %s or when the cluster restarts. " % code('pg_stat_reset()'),
 ""),
("Query-Level Observability: pg_stat_statements and Query Store",
 "Query-Level Observability: sys.dm_exec_query_stats and Query Store"),
("<strong class=\"text-white\">pg_stat_statements in PostgreSQL</strong>",
 "<strong class=\"text-white\">sys.dm_exec_query_stats in SQL Server</strong>"),
("""%s is a contrib extension that normalizes every query (replacing literal values with placeholders) and accumulates execution statistics per unique query shape. It must be loaded via %s and created with %s.""" % (code('pg_stat_statements'), code('shared_preload_libraries'), code('CREATE EXTENSION pg_stat_statements')),
 """%s accumulates execution statistics per cached plan — execution counts, worker time, logical reads, and elapsed time. It needs no extension and no configuration; it is always on. Its limitation is that it is in-memory and resets when the plan cache clears or the service restarts — which is exactly the gap Query Store fills.""" % code('sys.dm_exec_query_stats')),
("""The view exposes mean execution time, total time, rows returned, buffer hits, shared block reads, and — since PostgreSQL 14 — planning time separate from execution time. This separation matters because a query with a stable plan will have near-zero planning overhead, but a query whose statistics are stale will spend significant time replanning.""",
 """Because dm_exec_query_stats aggregates by plan handle, the same query text with different plans appears as separate rows. That is a feature for diagnosis: when a query suddenly slows down, the first check is whether a new plan handle appeared with worse numbers — the signature of a plan regression or parameter sniffing."""),
("""The %s column is often overlooked but tells you something important: a query with a high standard deviation is not just slow, it is *inconsistently* slow. That pattern usually points to parameter sniffing issues, plan instability, or lock contention that only hits some executions.""" % code('stddev_exec_time'),
 """The <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">total_worker_time</code> vs <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">total_elapsed_time</code> split is often overlooked but tells you something important: high elapsed time with low worker time means the query is *waiting* — on locks, I/O, or the network — not working. That pattern usually points to blocking, storage latency, or a downstream consumer that cannot keep up."""),
("<strong class=\"text-white\">PostgreSQL Wait Events</strong>",
 "<strong class=\"text-white\">SQL Server Wait Types</strong>"),
("""PostgreSQL exposes waits through %s and %s.""" % (code('pg_stat_activity.wait_event'), code('wait_event_type')),
 """SQL Server exposes waits through %s for live sessions and the cumulative %s.""" % (code('sys.dm_exec_requests.wait_type'), code('sys.dm_os_wait_stats'))),
("""**Lock**: Row-level or table-level lock contention — investigate `pg_locks` immediately""",
 """**LCK_M_X**: Lock contention — investigate `sys.dm_tran_locks` and the blocking chain immediately"""),
("""**LWLock:BufferMapping**: Heavy concurrent access to shared buffers; usually a sign of insufficient `shared_buffers` or extremely hot pages""",
 """**PAGEIOLATCH_SH**: Buffer pool miss, reading from disk; sustained high values mean the working set exceeds memory or storage is slow"""),
("""**IO:DataFileRead**: Buffer cache miss, reading from disk""",
 """**WRITELOG**: Waiting on transaction log writes — log drive latency or throughput bottleneck"""),
("""**Client:ClientRead**: Waiting for the application to send the next query — often long idle transactions""",
 """**ASYNC_NETWORK_IO**: Waiting for the application to consume results — often long client-side processing or a chatty ORM"""),
("Because %s is a snapshot, you cannot rely on a single query to characterize wait patterns." % code('pg_stat_activity'),
 "Because %s is a snapshot, you cannot rely on a single query to characterize wait patterns." % code('sys.dm_exec_requests')),
("""Tools like %s, %s, and %s do this sampling for you continuously""" % (code('pgBadger'), code('pganalyze'), code('Prometheus + postgres_exporter')),
 """Tools like SentryOne, Redgate Monitor, and %s do this sampling for you continuously""" % code('Prometheus + sql_exporter')),
("<strong class=\"text-white\">PostgreSQL auto_explain</strong>",
 "<strong class=\"text-white\">Extended Events: Slow Query Capture</strong>"),
("""%s is a contrib module that logs the execution plan of any query exceeding a configurable duration threshold. It must be loaded via %s. The key parameters:""" % (code('auto_explain'), code('shared_preload_libraries')),
 """Extended Events can capture the execution plan of any query exceeding a duration threshold, with far less overhead than the old SQL Trace. The key is a filtered event session on %s (or %s when you need the actual plan):""" % (code('sqlserver.sql_statement_completed'), code('query_post_execution_showplan'))),
("""<code>auto_explain.log_min_duration = '1s'
auto_explain.log_analyze = on
auto_explain.log_buffers = on
auto_explain.log_timing = on
auto_explain.log_format = 'json'
auto_explain.log_nested_statements = on</code>""",
 """<code>-- Capture plans for queries running longer than 5 seconds
CREATE EVENT SESSION slow_queries ON SERVER
ADD EVENT sqlserver.query_post_execution_showplan
(
    WHERE duration &gt; 5000000  -- microseconds
)
ADD TARGET package0.event_file
(
    SET filename = N'C:\\XEvents\\slow_queries.xel',
        max_file_size = 100,
        max_rollover_files = 5
)
WITH (MAX_MEMORY = 64MB, EVENT_RETENTION_MODE = ALLOW_SINGLE_EVENT_LOSS);
ALTER EVENT SESSION slow_queries ON SERVER STATE = START;</code>"""),
("""%s runs %s on every captured query, which adds execution overhead. In high-traffic systems, set %s high enough (5–10 seconds) to avoid capturing too many plans, or use %s (available since PostgreSQL 12) to capture a fraction of all queries regardless of duration — useful for identifying plans that are individually fast but have a bad shape at scale.""" % (code('log_analyze = on'), code('EXPLAIN ANALYZE'), code('log_min_duration'), code('auto_explain.sample_rate')),
 """Capturing the actual plan (%s) adds execution overhead, so in high-traffic systems keep the duration threshold high (5–10 seconds) or sample: use %s so a flood of slow queries drops events rather than stalling the server — useful for identifying plans that are individually tolerable but have a bad shape at scale.""" % (code('query_post_execution_showplan'), code('ALLOW_SINGLE_EVENT_LOSS'))),
("Both databases generate deadlock information through their event systems.",
 "SQL Server generates deadlock information through its event system."),
("""In PostgreSQL, deadlocks are logged to %s with %s and %s. The log entry includes the PIDs, the queries involved, and the lock types. For more structured capture, %s joined with %s gives you a live lock graph.""" % (code('postgresql.log'), code('log_lock_waits = on'), code('deadlock_timeout = 1s'), code('pg_stat_activity'), code('pg_locks')),
 """In SQL Server, deadlocks are captured automatically by the %s Extended Events session, which retains the deadlock graph XML on a rolling basis. For persistent capture, add the %s event to your own session. The graph shows the SPIDs, the statements involved, and the lock resources — everything needed to break the cycle. For live lock analysis, %s joined with %s gives you the current blocking chain.""" % (code('system_health'), code('xml_deadlock_report'), code('sys.dm_exec_requests'), code('sys.dm_tran_locks'))),
("table and index statistics every few minutes; checkpoint and bgwriter counters every minute. Anything more frequent than 10 seconds for most metrics will add non-trivial overhead to PostgreSQL's statistics collector and SQL Server's DMV queries.",
 "table and index statistics every few minutes; checkpoint counters every minute. Anything more frequent than 10 seconds for most metrics will add non-trivial overhead to the DMV queries themselves."),
("""For PostgreSQL, %s is the standard Prometheus integration point. It exposes %s, %s, %s, %s, and many other views as Prometheus metrics, which you then scrape into Grafana for dashboards. The %s and %s tools complement this for real-time session monitoring and log analysis respectively.""" % (code('postgres_exporter'), code('pg_stat_statements'), code('pg_stat_activity'), code('pg_stat_bgwriter'), code('pg_stat_replication'), code('pg_activity'), code('pgBadger')),
 """For SQL Server, %s (or Telegraf's sqlserver input plugin) is the standard Prometheus integration point. It exposes %s, wait stats, and Query Store-derived metrics as Prometheus metrics, which you then scrape into Grafana for dashboards.""" % (code('sql_exporter'), code('sys.dm_os_performance_counters'))),
("""graph LR
    PG[("PostgreSQL\\npg_stat_* views")] --> Exp1["postgres_exporter"]
    SQL[("SQL Server\\nDMVs")] --> Exp2["sql_exporter / Telegraf"]
    Exp1 --> Prom["Prometheus"]
    Exp2 --> Prom
    Prom --> Grafana["Grafana Dashboards"]
    Prom --> Alert["Alertmanager"]
    Alert --> OnCall["Slack / PagerDuty"]""",
 """graph LR
    SQL[("SQL Server\\nDMVs + Query Store")] --> Exp["sql_exporter / Telegraf"]
    XEv[("Extended Events")] --> Files["event_file targets"]
    Exp --> Prom["Prometheus"]
    Prom --> Grafana["Grafana Dashboards"]
    Prom --> Alert["Alertmanager"]
    Alert --> OnCall["Slack / PagerDuty"]"""),
("Buffer hit ratio drops below 95% (PostgreSQL: `pg_statio_user_tables`) — sustained drops indicate working set exceeds shared buffers",
 "Buffer cache hit ratio drops below 95% (`sys.dm_os_performance_counters`) — sustained drops indicate the working set exceeds the buffer pool"),
("Replication lag exceeds 30 seconds on a standby (PostgreSQL: `pg_stat_replication.replay_lag`; SQL Server: `sys.dm_hadr_database_replica_states`)",
 "Replication lag exceeds 30 seconds on a secondary (`sys.dm_hadr_database_replica_states`)"),
("Checkpoint completion ratio falling below 0.9 in PostgreSQL (indicating `checkpoint_completion_target` tuning may be needed or I/O is saturated)",
 "Checkpoint pages/sec spiking alongside rising `WRITELOG` waits (indicating I/O saturation on the log drive)"),
("**PostgreSQL's `pg_stat_statements` and SQL Server's Query Store** are the most important query-level observability tools in each engine, providing normalized, aggregated, and persistent execution statistics that point directly to the queries consuming the most resources.",
 "**Query Store** is the most important query-level observability tool in the engine, providing normalized, aggregated, and persistent execution statistics that point directly to the queries consuming the most resources."),
("**Extended Events (SQL Server) and `auto_explain` (PostgreSQL)** provide the deep, per-query tracing layer that aggregate statistics cannot.",
 "**Extended Events** provide the deep, per-query tracing layer that aggregate statistics cannot."),
("Tools like `postgres_exporter`, Telegraf, Prometheus, and Grafana turn the raw data exposed by each engine's internal views into a continuously available, historically queryable record",
 "Tools like `sql_exporter`, Telegraf, Prometheus, and Grafana turn the raw data exposed by the engine's DMVs into a continuously available, historically queryable record"),
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
    print(f'ch32: all {len(REPLACEMENTS)} replacements applied')

main()
