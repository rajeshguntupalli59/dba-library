#!/usr/bin/env python3
"""Rewrite ch40 as SQL Server-only, replacing the PG best-practices section with
Operational Excellence. Fails loudly on non-unique matches."""
import sys, re

PATH = '/home/hatch/workspace/dba-library/book/ch40-summary.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x):
    return '<code class="%s">%s</code>' % (C, x)
H3 = '<h3 class="text-lg font-semibold text-white mt-8 mb-3">%s</h3>'
P = '<p class="text-gray-300 leading-relaxed">%s</p>'

R = []

R.append((
    "how to operate PostgreSQL and SQL Server environments with the confidence and discipline that production systems demand.",
    "how to operate SQL Server environments with the confidence and discipline that production systems demand.",
))

R.append((
    "Default autovacuum settings, default memory allocations, default parallelism thresholds \u2014 all of these require tuning for production environments.",
    "Default auto-update statistics behavior, default memory allocations, default parallelism thresholds \u2014 all of these require tuning for production environments.",
))

R.append((
    "Despite the significant architectural differences between PostgreSQL and SQL Server, the fundamental principles of good database management apply equally to both. These principles have appeared throughout every chapter of this book in different forms.",
    "The fundamental principles of good database management have appeared throughout every chapter of this book in different forms.",
))

R.append((
    "When you increase " + code('work_mem') + " in PostgreSQL or change " + code('max degree of parallelism') + " in SQL Server,",
    "When you change " + code('max degree of parallelism') + " or " + code('cost threshold for parallelism') + " in SQL Server,",
))

R.append((
    "For PostgreSQL, this means knowing exactly how to execute a PITR (Point-in-Time Recovery) from your base backup and WAL archive, how long it takes, and what the first verification steps are after the database comes up. For SQL Server, this means knowing your full, differential, and transaction log backup chain, the order of restore operations, and how to verify database consistency with " + code('DBCC CHECKDB') + " after recovery.",
    "This means knowing your full, differential, and transaction log backup chain, the order of restore operations, how long each step takes, and how to verify database consistency with " + code('DBCC CHECKDB') + " after recovery.",
))

R.append((
    "On PostgreSQL, adding a column with a non-null default triggers a table rewrite in versions before PostgreSQL 11. On SQL Server, adding a nullable column to a large table is metadata-only in modern versions, but adding a non-null column with no default still requires touching every row.",
    "Adding a nullable column to a large table is metadata-only in modern versions, but adding a non-null column with no default still requires touching every row.",
))

R.append((
    "PostgreSQL streaming replication standbys can serve read queries, distributing analytical or reporting load away from the primary. SQL Server Always On Availability Groups with readable secondaries serve the same purpose.",
    "Always On Availability Groups with readable secondaries can serve read queries, distributing analytical or reporting load away from the primary.",
))

R.append((
    "Understanding how PostgreSQL's MVCC model affects vacuum requirements, or how SQL Server's locking architecture drives blocking patterns,",
    "Understanding how SQL Server's locking architecture drives blocking patterns, or how the storage engine handles page splits and fragmentation,",
))

R.append((
    "Whether you are using `EXPLAIN ANALYZE` in PostgreSQL or the graphical execution plan in SQL Server Management Studio,",
    "Whether you are reading the graphical execution plan in SQL Server Management Studio or the XML showplan,",
))

# --- Operational Excellence section replaces the PG best-practices block ---
OE = []
OE.append(H3 % "Operational Excellence: The Habits of a Well-Run SQL Server Shop")
OE.append(P % "Operational excellence is not a feature you enable \u2014 it is the set of rhythms that separates shops that page at 3 AM from shops that sleep. Across every chapter of this book, a handful of disciplines kept reappearing. This section consolidates them into the daily, weekly, and monthly habits of a well-run SQL Server environment.")
OE.append(P % "<strong class=\"text-white\">Query Store is your flight recorder.</strong> Enable Query Store on every user database \u2014 it is the one feature that turns \"the database was slow yesterday afternoon\" from a mystery into a timeline. Query Store captures query text, execution plans, and runtime statistics over time, so you can see exactly which query regressed, when it changed plans, and what the old plan looked like. The daily habit is simple: open the Regressed Queries view, look for queries whose duration or CPU jumped, and compare plans before and after the regression point. When a bad plan is actively hurting production, plan forcing buys you time \u2014 pin the known-good plan while you investigate the root cause (usually stale statistics or a parameter sniffing issue). Set a retention window that covers at least two full business cycles so regressions tied to month-end or quarterly batch jobs are still in the record when you go looking. A Query Store that is off, or one whose data has already aged out, is no flight recorder at all.")
OE.append(P % "<strong class=\"text-white\">Readable secondaries are a load-balancing strategy, not an accident.</strong> Always On Availability Groups let you offload reporting and analytics to readable secondaries, but the separation has to be designed. Configure read-only routing on the listener so application connections land on secondaries automatically; otherwise every report still hits the primary. Set consistency expectations explicitly: secondary data is seconds behind the primary, and redo queue growth during maintenance can stretch that to minutes. And remember that queries on a readable secondary run under snapshot isolation semantics, which adds row versioning overhead on the primary \u2014 test the read workload against a secondary before you declare the separation a success.")
OE.append(P % "<strong class=\"text-white\">DBCC CHECKDB is a scheduled discipline.</strong> Run CHECKDB on a regular schedule \u2014 weekly for critical databases \u2014 and understand its cost: it is I/O-heavy, and on very large databases the full check may not fit inside a maintenance window. The standard adaptations are " + code('PHYSICAL_ONLY') + " for a fast nightly pass that catches hardware-level corruption, the full logical check weekly or against a restored backup copy, and on very large databases, running the full CHECKDB against last night's backup restore rather than the live database. A CHECKDB failure is a stop-everything event: corruption does not heal, and every hour you delay the response is an hour of new transactions built on damaged pages.")
OE.append(P % "<strong class=\"text-white\">Backups are a chain, not a job.</strong> The rhythm that works for most production databases: a full backup weekly, differentials daily, and transaction log backups every fifteen minutes. Know the restore order cold \u2014 full, most recent differential, then every log backup in sequence \u2014 and practice it, because the restore you have never rehearsed is the restore that will surprise you. Run " + code('RESTORE VERIFYONLY') + " after backups to catch media problems early, and run a full restore drill to a non-production server quarterly: restore the chain, run CHECKDB against the restored copy, and confirm the application can actually use the data. Log backup frequency is also your RPO knob \u2014 fifteen minutes of acceptable data loss means fifteen-minute log backups, no exceptions.")
OE.append(P % "<strong class=\"text-white\">Availability groups need health checks, not just configuration.</strong> An availability group that was configured correctly six months ago can be unhealthy today: redo queues grow, synchronization falls behind, a replica runs out of disk. Build a weekly health check around " + code('sys.dm_hadr_database_replica_states') + " \u2014 synchronization state, log send queue, redo queue \u2014 and alert on drift, not just failure. Run a failover drill quarterly so the procedure is muscle memory rather than a runbook you are reading for the first time at 2 AM. And respect quorum: understand what happens to availability when you lose a node, and never let a two-node cluster with a file share witness become a single point of failure you forgot about.")
OE.append(P % "These five habits compound. Query Store tells you what regressed; readable secondaries keep the primary healthy enough to serve the workload; CHECKDB and the backup chain mean you can survive corruption and failure; availability group health checks mean failover works when you need it. None of them is exotic. All of them are the difference between a shop that reacts and a shop that operates.")
OE.append('<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- Query Store flight recorder: worst regressed queries in the last 7 days\nSELECT TOP 20\n    qst.query_sql_text,\n    rs.avg_duration / 1000.0 AS avg_duration_ms,\n    rs.avg_cpu_time / 1000.0 AS avg_cpu_ms,\n    rs.count_executions,\n    rs.last_execution_time\nFROM sys.query_store_query_text qst\nJOIN sys.query_store_query q ON qst.query_text_id = q.query_text_id\nJOIN sys.query_store_plan p ON q.query_id = p.query_id\nJOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id\nWHERE rs.last_execution_time &gt;= DATEADD(day, -7, SYSDATETIME())\nORDER BY rs.avg_duration DESC;</code></pre>')
OE_BLOCK = "\n\n\n".join(OE)

def main():
    text = open(PATH).read()
    for i, (old, new) in enumerate(R):
        count = text.count(old)
        if count != 1:
            print('FAIL replacement %d: found %d occurrences' % (i, count))
            print('OLD SNIPPET:', old[:160])
            sys.exit(1)
        text = text.replace(old, new, 1)
    # Replace the PG best-practices section: from its h3 to the '---' before SQL Server best practices
    start_marker = H3 % "PostgreSQL Best Practices: The Lessons That Matter Most"
    end_marker = H3 % "SQL Server Best Practices: The Lessons That Matter Most"
    si = text.find(start_marker)
    ei = text.find(end_marker)
    if si == -1 or ei == -1 or ei < si:
        print('FAIL: could not locate PG section boundaries'); sys.exit(1)
    text = text[:si] + OE_BLOCK + "\n\n\n" + text[ei:]
    open(PATH, 'w').write(text)
    print('ch40: %d phrase replacements + Operational Excellence section applied' % len(R))

main()
