#!/usr/bin/env python3
"""Apply ch13 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch13-monitoring.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
def LI(x): return '<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> %s</li>' % x

DMV_SECTION = """<p class="text-gray-300 leading-relaxed"><strong class="text-white">Essential DMVs for Monitoring</strong></p>

<p class="text-gray-300 leading-relaxed">SQL Server's DMVs reset on service restart — they're a window into current activity, not history. (Query Store fills the history gap; see below.) The ones worth memorizing:</p>

%s
%s
%s
%s
%s
%s

<p class="text-gray-300 leading-relaxed">The discipline that separates good monitoring from dashboard collection: snapshot the key DMVs into a DBA utility database on a schedule. A 5-minute sampling of %s, %s, and file-level I/O gives you the history the DMVs don't keep — and it's the data you'll wish you had during the next post-mortem.</p>
""" % (
 LI('%s — currently executing requests: wait type, wait time, CPU, logical reads, blocking session id' % code('sys.dm_exec_requests')),
 LI('%s — cumulative waits since restart; the basis of wait-statistics analysis' % code('sys.dm_os_wait_stats')),
 LI('%s — aggregated query performance by plan; your top-offender finder' % code('sys.dm_exec_query_stats')),
 LI('%s — index seek/scan/lookup/update counts for usage analysis' % code('sys.dm_db_index_usage_stats')),
 LI('%s — fragmentation and page counts' % code('sys.dm_db_index_physical_stats')),
 LI('%s — the PerfMon counters exposed as a DMV (batch requests, compilations, page life expectancy)' % code('sys.dm_os_performance_counters')),
 code('sys.dm_os_wait_stats'), code('sys.dm_exec_query_stats'),)

MAINT_SECTION = """<h3 class="text-lg font-semibold text-white mt-8 mb-3">Index Fragmentation, Statistics Freshness, and Maintenance Monitoring in SQL Server</h3>

<p class="text-gray-300 leading-relaxed">SQL Server has no autovacuum — maintenance is explicit, usually driven by SQL Server Agent jobs (Ola Hallengren's scripts being the community standard). That makes monitoring the maintenance itself a core DBA responsibility: a failed index-maintenance job pages nobody by itself, and fragmentation silently accumulates until queries slow down and someone blames the storage team.</p>

<p class="text-gray-300 leading-relaxed">Three things to watch. First, <strong class="text-white">index fragmentation</strong> via %s. Second, <strong class="text-white">statistics freshness</strong>: stale statistics are the number-one cause of sudden plan regressions, and auto-update doesn't always keep up on large or skewed tables. %s tells you when each statistics object was last updated — anything business-critical older than your maintenance window deserves attention:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- SQL Server: find stale statistics on large tables
SELECT
    OBJECT_SCHEMA_NAME(s.object_id) + '.' + OBJECT_NAME(s.object_id) AS table_name,
    s.name                              AS stats_name,
    STATS_DATE(s.object_id, s.stats_id) AS last_updated,
    DATEDIFF(DAY, STATS_DATE(s.object_id, s.stats_id), GETDATE()) AS days_old,
    sp.rows
FROM sys.stats AS s
JOIN sys.partitions AS p ON p.object_id = s.object_id AND p.index_id IN (0, 1)
CROSS APPLY sys.dm_db_partition_stats AS ps
CROSS APPLY (SELECT SUM(ps2.row_count) AS rows FROM sys.dm_db_partition_stats ps2
             WHERE ps2.object_id = s.object_id) AS sp
WHERE s.auto_created = 0
  AND STATS_DATE(s.object_id, s.stats_id) &lt; DATEADD(DAY, -7, GETDATE())
ORDER BY days_old DESC;</code></pre>

<p class="text-gray-300 leading-relaxed">Third, <strong class="text-white">job health</strong>: %s shows whether last night's maintenance actually ran. A green dashboard with a silently failing rebuild job is how 90%% fragmentation happens "suddenly". Alert on any failed Agent job in the last 24 hours — not just maintenance jobs, because a failed backup job is the one you'll regret most.</p>

<p class="text-gray-300 leading-relaxed">The fragmentation query below is the standard starting point — run it against your largest tables first, since that's where fragmentation hurts most:</p>
""" % (code('sys.dm_db_index_physical_stats'), code('STATS_DATE()'), code('msdb.dbo.sysjobhistory'))

QS_DEEP_DIVE = """<p class="text-gray-300 leading-relaxed"><strong class="text-white">Query Store Deep Dive: Plan Forcing and Regression Detection</strong></p>

<p class="text-gray-300 leading-relaxed">Where Query Store earns its keep is plan forcing: when a query regresses to a bad plan, %s pins the last known-good plan while you fix the root cause (usually statistics or a missing index). Query Store also makes "what changed last night" answerable — the regressed-queries report diffs plan performance across time intervals, so a 3 a.m. slowdown gets attributed to a specific plan change instead of a vague "the database is slow".</p>

<p class="text-gray-300 leading-relaxed">Two caveats. First, Query Store has its own storage quota (%s) — when full it flips to read-only and silently stops collecting. Monitor %s for %s. Second, on AG secondaries Query Store data is per-replica; a forced plan on the primary doesn't replicate the forcing to secondaries, so verify behavior where the workload actually runs.</p>
""" % (code('sp_query_store_force_plan'), code('MAX_STORAGE_SIZE_MB'), code('sys.database_query_store_options'), code('actual_state_desc'))

REPLACEMENTS = [
# 1 intro
("""how to build alerts that are useful rather than noisy, and how to construct the kind of observability infrastructure that keeps production systems healthy and recoverable.""",
 """how to build alerts that are useful rather than noisy, and how to construct the kind of observability infrastructure that keeps production SQL Server systems healthy and recoverable."""),
("""how to monitor it effectively in both PostgreSQL and SQL Server,""",
 """how to monitor it effectively in SQL Server,"""),

# 2 correctness
("""Are autovacuum and maintenance jobs running on schedule?""",
 """Are Agent maintenance jobs running on schedule?"""),

# 3 h3 core metrics
("""Core Metrics: What PostgreSQL and SQL Server Expose""",
 """Core Metrics: What SQL Server Exposes"""),

# 12 connections
("""A sudden spike in idle-in-transaction connections in PostgreSQL, or a surge of suspended sessions in SQL Server, almost always indicates a lock contention issue or a misbehaving application that is not committing or closing transactions properly.""",
 """A surge of suspended or runnable sessions almost always indicates a lock contention issue or a misbehaving application that is not committing or closing transactions properly."""),

# 13 buffer cache
("""A healthy PostgreSQL buffer cache hit ratio should be above 98–99%% for an OLTP workload with a properly sized %s. In SQL Server, a Buffer Cache Hit Ratio below 95%% on a production OLTP system is worth investigating.""" % code('shared_buffers'),
 """In SQL Server, a Buffer Cache Hit Ratio below 95% on a production OLTP system is worth investigating — but treat it as a supporting signal, not a diagnosis. A low ratio on a data-warehouse workload doing large scans is normal; a falling ratio on an OLTP workload that used to sit at 99% is not."""),

# 14 blocking
("""In PostgreSQL, blocking appears through %s joined with %s. In SQL Server, blocking is exposed through %s and the dedicated %s DMV.""" % (code('pg_locks'), code('pg_stat_activity'), code('sys.dm_exec_requests'), code('sys.dm_os_waiting_tasks')),
 """In SQL Server, blocking is exposed through %s and the dedicated %s DMV — join them to build the blocking chain from lead blocker down to every waiter.""" % (code('sys.dm_exec_requests'), code('sys.dm_os_waiting_tasks'))),

# 15 wait stats
("""In PostgreSQL, %s shows per-session wait events through the %s and %s columns. There is no cumulative wait stats view equivalent to SQL Server's %s in vanilla PostgreSQL, though extensions like %s can be added to capture this data over time.""" % (code('pg_stat_activity'), code('wait_event_type'), code('wait_event'), code('dm_os_wait_stats'), code('pg_wait_sampling')),
 """%s is the cumulative wait-statistics view — the foundation of wait-based performance analysis. Sample it on an interval and diff the snapshots: the top waits tell you what the instance is actually waiting on (<strong class="text-white">PAGEIOLATCH_*</strong> means storage, <strong class="text-white">CXPACKET/CXCONSUMER</strong> means parallelism, <strong class="text-white">LCK_*</strong> means blocking). Per-session, %s shows the current wait type live.""" % (code('sys.dm_os_wait_stats'), code('sys.dm_exec_requests'))),

# 24 duration triggering
("""If CPU spikes to 90% for 10 seconds during an autovacuum run, that is not worth waking someone up.""",
 """If CPU spikes to 90% for 10 seconds during an index rebuild, that is not worth waking someone up."""),

# alert table rows
("""| XID age (PostgreSQL) | > 500M | > 1.5B |""",
 """| Index fragmentation (largest tables) | > 30% avg | > 50% or maintenance job failing |"""),
("""| Autovacuum failures | Any | Any |""",
 """| Statistics age (critical tables) | > 7 days | > 30 days |\n<p class="text-gray-300 leading-relaxed">| Failed Agent jobs | Any in 24h | Any backup/maintenance job |</p>"""),

# 27 PG tools -> SQL Server OSS
("""For PostgreSQL, <strong class="text-white">pgBadger</strong> parses log files and produces detailed HTML reports on slow queries, lock waits, and connection patterns. It is excellent for after-the-fact analysis but does not provide real-time monitoring. <strong class="text-white">pg_activity</strong> is a top-like tool for watching live PostgreSQL activity from the command line. For more comprehensive monitoring, <strong class="text-white">Prometheus with postgres_exporter</strong> has become the dominant open-source stack: postgres_exporter scrapes %s views on a configurable interval, exposes metrics in Prometheus format, and feeds into <strong class="text-white">Grafana</strong> dashboards for visualization and alerting. Community-built Grafana dashboards for PostgreSQL are available on grafana.com and provide an excellent starting point.""" % code('pg_stat_*'),
 """For SQL Server, the open-source stack centers on Telegraf's SQL Server input plugin or the Prometheus sql_exporter, feeding <strong class="text-white">Grafana</strong> dashboards — community SQL Server dashboards on grafana.com cover waits, buffer pool, and AG health out of the box. <strong class="text-white">Extended Events</strong> is the built-in tracing framework: lightweight, always available, and the right tool for capturing deadlocks (the system_health session), slow queries, and wait accumulation without Profiler's overhead."""),

# 31 monitoring script
("""A typical structure for a PostgreSQL monitoring script might be a Python or bash script that connects via %s, runs a set of diagnostic queries, compares results to hardcoded or config-file-defined thresholds, and posts to a Slack webhook if any threshold is breached. The script runs every 5 minutes via cron. This approach is low-cost, transparent, and entirely under your control.""" % code('psql'),
 """A typical structure for a SQL Server monitoring script is a PowerShell script using the SqlServer module — or <strong class="text-white">dbatools</strong>, the community-standard PowerShell module — that runs diagnostic queries, compares results to thresholds, and posts to a Slack webhook or sends Database Mail on breach. The script runs every 5 minutes via SQL Server Agent or Task Scheduler. dbatools deserves special mention: it turns multi-instance monitoring (backups, disk space, job health, version inventory) from a project into a one-liner, and every DBA managing more than a handful of instances should know it."""),

# 32 takeaway metrics
("""Both PostgreSQL and SQL Server expose rich internal metrics through system views and DMVs; the `pg_stat_*` family in PostgreSQL and the `sys.dm_*` DMV family in SQL Server are your primary data sources for everything from connection counts to query performance.""",
 """SQL Server exposes rich internal metrics through DMVs; the `sys.dm_*` family is your primary data source for everything from connection counts to query performance — but DMVs reset on restart, so snapshot what matters into a utility database instead of trusting them as history."""),

# 33 takeaway maintenance
("""PostgreSQL carries a maintenance risk SQL Server does not: MVCC dead tuple accumulation and, in the extreme case, transaction ID wraparound. Monitoring dead tuple ratios, autovacuum activity, and `age(datfrozenxid)` is not optional — an unmonitored wraparound risk can take a database offline entirely.""",
 """SQL Server has no autovacuum — maintenance is explicit and job-driven, which means monitoring the maintenance itself is the DBA's job: watch fragmentation via `sys.dm_db_index_physical_stats`, statistics age via `STATS_DATE()`, and Agent job history for the silent failures that hurt the most."""),

# 34 takeaway query store
("""Query Store (SQL Server) and `pg_stat_statements` (PostgreSQL) are the two most valuable built-in tools for understanding workload behavior over time, and both should be enabled on every production database rather than left as an afterthought discovered only when a plan regression is already causing pain.""",
 """Query Store is the most valuable built-in tool for understanding workload behavior over time — enable it on every production database, learn plan forcing for emergency regressions, and monitor its storage state rather than discovering problems only when they're already causing pain."""),
]

def main():
    lines = open(PATH).read().split('\n')
    # 1. Replace PG pg_stat_* subsection (lines 73-83, 1-indexed) with DMV section.
    assert 'PostgreSQL System Catalog and Statistics Views' in lines[72], lines[72][:80]
    assert 'SQL Server Dynamic Management Views' in lines[83], lines[83][:80]
    lines = lines[:72] + [DMV_SECTION] + lines[83:]
    # 2. Replace bloat h3 section (h3 at 163) through line 185 with maintenance section.
    idx_h3 = next(i for i, l in enumerate(lines) if 'Table Bloat, Autovacuum, and Maintenance Monitoring in PostgreSQL' in l)
    assert 'Alert when' in lines[idx_h3 + 21] or 'xid_age' in lines[idx_h3 + 21], lines[idx_h3 + 21][:80]
    # find the paragraph starting with "SQL Server does not have an equivalent"
    idx_sql = next(i for i, l in enumerate(lines) if 'SQL Server does not have an equivalent of autovacuum' in l)
    new_para = '<p class="text-gray-300 leading-relaxed">The fragmentation query below is the standard starting point — run it against your largest tables first, since that is where fragmentation hurts most:</p>'
    lines = lines[:idx_h3] + [MAINT_SECTION] + [new_para] + lines[idx_sql + 1:]
    # 3. Replace pg_stat_statements section with Query Store deep dive.
    text = '\n'.join(lines)
    pg_ss_header = '<strong class="text-white">pg_stat_statements in PostgreSQL</strong>'
    auto_header = '<strong class="text-white">Automated Alerting with Scripts and Jobs</strong>'
    i1 = text.find(pg_ss_header)
    i2 = text.find(auto_header)
    assert i1 != -1 and i2 != -1 and i2 > i1
    pstart = text.rfind('<p class="text-gray-300 leading-relaxed">', 0, i1)
    pend = text.rfind('<p class="text-gray-300 leading-relaxed">', 0, i2)
    text = text[:pstart] + QS_DEEP_DIVE + '\n' + text[pend:]
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch13: 3 sections replaced + all {len(REPLACEMENTS)} replacements applied')

main()
