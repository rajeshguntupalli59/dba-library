#!/usr/bin/env python3
"""Apply ch29 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch29-orchestration.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 intro
("""This chapter covers the core concepts of orchestration as they apply to PostgreSQL and SQL Server, from basic job scheduling through to multi-step pipeline coordination using modern tools""",
 """This chapter covers the core concepts of orchestration as they apply to SQL Server, from basic job scheduling through to multi-step pipeline coordination using modern tools"""),

# 2 motivation VACUUM
("""First, maintenance operations grow in complexity as databases scale. A single VACUUM ANALYZE on a small table is trivial. Coordinating VACUUM operations across hundreds of tables, prioritizing bloat, avoiding conflicts with long-running transactions, and logging outcomes is not.""",
 """First, maintenance operations grow in complexity as databases scale. A single UPDATE STATISTICS on a small table is trivial. Coordinating index maintenance across hundreds of tables, prioritizing by fragmentation, avoiding conflicts with long-running transactions, and logging outcomes is not."""),

# 3 native scheduling both
("""Both PostgreSQL and SQL Server ship with or have closely associated native scheduling tools, and every DBA should know them deeply even if they eventually move beyond them.""",
 """SQL Server ships with a native scheduling tool, and every DBA should know it deeply even if they eventually move beyond it."""),

# h3 native scheduling
("""Native Scheduling: pgAgent, SQL Server Agent, and Their Limits""",
 """Native Scheduling: SQL Server Agent and Its Limits"""),

# 4 pgAgent para -> Agent limits bridge
("""<strong class="text-white">pgAgent</strong> is a companion tool for PostgreSQL, installed separately and typically managed through pgAdmin. It supports multi-step jobs with steps written in SQL or shell script, scheduled using cron-style expressions. Job history is stored in the %s schema within a nominated database. pgAgent is functional but less feature-rich than SQL Server Agent — there is no native conditional branching between steps, and alerting capabilities are minimal unless extended externally.""" % code('pgagent'),
 """SQL Server Agent covers the single-instance scheduling need well: multi-step jobs with per-step retry logic, schedules, operators, and alerts are enough for most maintenance. Its limits appear when workflows span instances, need conditional branching across steps, or must coordinate with non-database systems — which is where the DAG-based tools in the next section take over."""),

# 5 Airflow/Prefect/Dagster
("""All three can orchestrate SQL tasks directly — executing queries against PostgreSQL or SQL Server as part of a larger pipeline — and all three provide a web UI for monitoring pipeline runs, inspecting logs, and manually retrying failed tasks.""",
 """All three can orchestrate SQL tasks directly — executing queries against SQL Server as part of a larger pipeline — and all three provide a web UI for monitoring pipeline runs, inspecting logs, and manually retrying failed tasks."""),

# 6 VACUUM timing assumption
("""A VACUUM step that "always finishes before the backup starts" because they run at 1 AM and 2 AM respectively is not an orchestrated dependency — it is a timing assumption waiting to be violated on a night when VACUUM runs long.""",
 """An index-maintenance step that "always finishes before the backup starts" because they run at 1 AM and 2 AM respectively is not an orchestrated dependency — it is a timing assumption waiting to be violated on a night when the rebuild runs long."""),

# 7 h3 maintenance pipelines
("""Coordinating Maintenance Pipelines Across PostgreSQL and SQL Server""",
 """Coordinating Maintenance Pipelines"""),

# 8 maintenance list
("""The most common orchestration work a DBA does is coordinating database maintenance — backup, VACUUM or update statistics, index rebuild or reorganize, and integrity checks — in a way that respects dependencies, respects maintenance windows, and generates auditable records. Here is how that coordination looks in practice for each platform.""",
 """The most common orchestration work a DBA does is coordinating database maintenance — backup, update statistics, index rebuild or reorganize, and integrity checks via DBCC CHECKDB — in a way that respects dependencies, respects maintenance windows, and generates auditable records. Here is how that coordination looks in practice."""),

# 9 PG pipeline
("""For <strong class="text-white">PostgreSQL</strong>, a production maintenance pipeline typically includes: identifying bloated tables programmatically, running VACUUM ANALYZE on high-priority targets, rebuilding indexes concurrently for the most bloated, and capturing before/after metrics. The programmatic identification step is itself a query that becomes part of the orchestration:""",
 """For <strong class="text-white">SQL Server</strong>, a production maintenance pipeline typically includes: identifying fragmented indexes programmatically, rebuilding or reorganizing by fragmentation level, updating statistics, running DBCC CHECKDB, and capturing before/after metrics. The programmatic identification step is itself a query that becomes part of the orchestration:"""),

# 10 n_dead_tup
("""This query is the first task in a pipeline. An orchestration tool runs it, captures the result set, and passes the list of table names to subsequent VACUUM tasks — potentially running several in parallel with a configurable concurrency limit to avoid overwhelming the server. After each VACUUM, a verification task checks that %s has decreased and logs the result. This is not possible with a static cron-scheduled script, because the set of tables to process is dynamic.""" % code('n_dead_tup'),
 """This query is the first task in a pipeline. An orchestration tool runs it, captures the result set, and passes the list of indexes to subsequent rebuild tasks — potentially running several in parallel with a configurable concurrency limit to avoid overwhelming the server. After each rebuild, a verification task re-checks fragmentation via %s and logs the result. This is not possible with a static Agent schedule, because the set of indexes to process is dynamic.""" % code('sys.dm_db_index_physical_stats')),

# 11 MERGE/upsert
("""For SQL Server, the %s statement or conditional %s/%s patterns provide idempotency in data loading steps. For PostgreSQL, %s (upsert) handles the same scenario:""" % (code('MERGE'), code('INSERT'), code('UPDATE'), code('INSERT ... ON CONFLICT DO UPDATE')),
 """For SQL Server, the %s statement or conditional %s/%s patterns provide idempotency in data loading steps:""" % (code('MERGE'), code('INSERT'), code('UPDATE'))),

# 12 VACUUM retry
("""A VACUUM that fails because of a conflicting lock should retry with exponential backoff — perhaps three times with intervals of 5 minutes, 15 minutes, and 45 minutes.""",
 """An index rebuild that fails because of a conflicting lock should retry with exponential backoff — perhaps three times with intervals of 5 minutes, 15 minutes, and 45 minutes."""),
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
    print(f'ch29: all {len(REPLACEMENTS)} replacements applied')

main()
