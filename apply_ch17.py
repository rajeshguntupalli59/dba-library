#!/usr/bin/env python3
"""Apply ch17 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch17-api.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 connection overhead
("""Establishing a PostgreSQL or SQL Server connection involves TCP handshaking, authentication, session initialization, and memory allocation on the server — often 5–50ms of overhead that adds up fast.""",
 """Establishing a SQL Server connection involves TCP handshaking, authentication, session initialization, and memory allocation on the server — often 5–50ms of overhead that adds up fast."""),

# 2 poolers
("""Connection poolers sit between the application and the database, maintaining a pool of pre-established connections that can be handed to incoming requests. PgBouncer is the dominant solution in the PostgreSQL ecosystem. SQL Server applications typically rely on ADO.NET connection pooling built into the .NET runtime, or external proxies like ProxySQL in heterogeneous stacks.""",
 """Connection pooling sits between the application and the database, maintaining a pool of pre-established connections handed to incoming requests. SQL Server applications rely on ADO.NET/SqlClient connection pooling built into the .NET runtime — enabled by default, keyed by the exact connection string, governed by %s and %s. ODBC and JDBC drivers pool the same way. The key DBA-visible point: pooling is per application process, so a fleet of app servers multiplies the real connection count — size pools against the fleet, not a single instance.""" % (code('Min Pool Size'), code('Max Pool Size'))),

# 3 visibility
("""In PostgreSQL, %s shows every backend process and what it is doing. In SQL Server, %s provides equivalent visibility.""" % (code('pg_stat_activity'), code('sys.dm_exec_sessions')),
 """In SQL Server, %s shows every session and what it is doing; join it to %s for the currently executing batch.""" % (code('sys.dm_exec_sessions'), code('sys.dm_exec_requests'))),

# 4 pool modes -> sp_reset_connection
("""Understanding the pool mode matters too. PgBouncer offers three modes: session pooling (a connection is held for the full client session), transaction pooling (the server connection is returned to the pool after each transaction), and statement pooling (after each statement). Transaction pooling is the most efficient for stateless API services but has restrictions — prepared statements behave differently, and SET commands that modify session-level configuration can leak state between requests unless the pooler resets the session. DBAs who deploy PgBouncer in transaction mode and then receive complaints about inconsistent behavior from developers need to check whether the application is relying on session-level settings that aren't surviving across requests.""",
 """Understanding what happens when a pooled connection is reused matters too. When SqlClient returns a connection to the pool and hands it out again, the driver issues %s — a lightweight server-side reset that rolls back open transactions, drops temp tables, and reverts most SET options. It does not reset everything: some session state can leak between checkouts if the application set options the reset doesn't cover. DBAs who get complaints about inconsistent behavior across requests need to check whether the application is relying on session-level settings that aren't surviving the reset — the fix is to set required options explicitly per batch, not to assume they persist.""" % code('sp_reset_connection')),

# 5 max connections
("""One thing worth tracking is the maximum connections setting. In PostgreSQL, each connection spawns a separate OS process that consumes shared memory and file descriptors. Setting %s to 1000 doesn't mean 1000 concurrent connections are free — each one costs real RAM. A rough rule of thumb is 5–10MB per connection in a moderately active system, meaning 500 connections can cost 2.5–5GB just in process overhead before a single query runs. PgBouncer's value is that it lets you maintain a small number of actual server connections while serving hundreds or thousands of application threads.""" % code('max_connections'),
 """One thing worth tracking is connection count against worker-thread capacity. In SQL Server each connection consumes a worker thread; %s scales with CPU count, but thousands of concurrently active connections still cause scheduler contention. The database handles hundreds of connections comfortably — but each idle connection still costs memory and each active one costs a worker. Size pools (%s) from measured concurrency, not guesswork, and watch %s for runnable-queue buildup that signals thread pressure.""" % (code('max worker threads'), code('Max Pool Size'), code('sys.dm_os_schedulers'))),

# 6 literals
("""When a query arrives at PostgreSQL or SQL Server with a hardcoded literal, the query planner treats each unique literal as a potentially unique query and may parse and plan it separately.""",
 """When a query arrives at SQL Server with a hardcoded literal, the optimizer treats each unique literal as a potentially unique query and may compile it separately — flooding the plan cache with single-use plans."""),

# 7 pg_stat_statements -> Query Store
("""In PostgreSQL, the server uses the %s extension to track query performance. Parameterized queries from applications using server-side prepared statements appear with their parameter placeholders intact, making it easy to identify slow query patterns. Ad-hoc queries with literal values get normalized by %s anyway — it replaces literals with %s, %s, etc. — but server-prepared statements go further by actually caching the plan on the connection.""" % (code('pg_stat_statements'), code('pg_stat_statements'), code('$1'), code('$2')),
 """In SQL Server, Query Store tracks query performance by query hash — parameterized queries appear with their parameter placeholders intact (as %s, %s), making it easy to identify slow query patterns. Ad-hoc queries with literals get normalized too, but parameterized batches go further: the plan cache reuses the compiled plan across executions, saving compile overhead on every subsequent call.""" % (code('@P1'), code('@P2'))),

# 8 generic plan -> parameter sniffing
("""The PostgreSQL equivalent is the generic plan problem. For extended query protocol prepared statements, PostgreSQL initially generates a custom plan (using the actual parameter values) for the first five executions, then switches to a generic plan if the estimated cost is comparable. If the generic plan is substantially worse for some parameter values, you can influence this behavior with the %s setting (available from PostgreSQL 12).""" % code('plan_cache_mode'),
 """The SQL Server version of this problem is parameter sniffing: the first execution's parameter values shape the cached plan, and later executions with very different values can get a terrible plan. The mitigations live in the usual toolbox — %s, %s hints, plan guides, Query Store forced plans — but the DBA's first job is recognizing the signature: one query, wildly varying runtimes, same plan hash.""" % (code('OPTION (RECOMPILE)'), code('OPTIMIZE FOR'))),

# 9 long transactions
("""In PostgreSQL, long-running transactions also block autovacuum from reclaiming dead tuples, which leads to table bloat and eventual transaction ID wraparound — one of the more severe operational hazards in PostgreSQL.""",
 """In SQL Server, long-running transactions also block version-store cleanup under row-versioning isolation (RCSI/snapshot), which bloats tempdb — and they hold locks that block everyone else for the duration."""),

# 10 savepoints
("""Savepoints are a useful but underused feature in API-driven transaction design. They allow an application to mark a point within a transaction to which it can roll back partially, without aborting the entire transaction. PostgreSQL supports savepoints natively. SQL Server calls them partial rollbacks using %s.""" % code('SAVE TRANSACTION'),
 """Savepoints are a useful but underused feature in API-driven transaction design. They allow an application to mark a point within a transaction to which it can roll back partially, without aborting the entire transaction. SQL Server supports them as partial rollbacks: %s marks the point, %s rolls back to it.""" % (code('SAVE TRANSACTION'), code('ROLLBACK TRANSACTION savepoint_name'))),

# 11 transaction-mode nuance
("""One nuance specific to connection pools operating in transaction mode (PgBouncer being the most common example): if an application begins a transaction and then crashes or loses its connection before committing, the pooler will roll back the transaction when it reclaims the connection — but this behavior depends on pool configuration, and in some setups orphaned transactions can hold locks until the idle connection timeout fires. Building retry logic and monitoring for blocked queries are both essential defenses.""",
 """One nuance specific to pooled connections: if an application begins a transaction and then crashes or loses its connection before committing, %s rolls back the orphaned transaction when the connection is reclaimed — but until that connection is reused, its locks can linger. Building retry logic and monitoring for blocked queries (%s with a non-null %s) are both essential defenses.""" % (code('sp_reset_connection'), code('sys.dm_exec_requests'), code('blocking_session_id'))),

# 12 multi-row insert
("""Most drivers support this transparently when you use their batch insert APIs. Both PostgreSQL and SQL Server handle multi-row inserts efficiently.""",
 """Most drivers support this transparently when you use their batch insert APIs. SQL Server handles multi-row inserts efficiently — one round trip, one transaction, one log stream."""),

# 13 COPY
("""For very large volumes, PostgreSQL's %s command is the fastest ingestion mechanism available. It bypasses much of the per-row overhead of individual INSERT statements and is optimized for streaming large datasets. On the SQL Server side, %s or the SqlBulkCopy API in .NET provides equivalent bulk load capability.""" % (code('COPY'), code('BULK INSERT')),
 """For very large volumes, the SqlBulkCopy API in .NET (or %s / %s) is the fastest ingestion mechanism available. It bypasses much of the per-row overhead of individual INSERT statements and is optimized for streaming large datasets — and with minimal-logging prerequisites met, it keeps the transaction log lean too.""" % (code('BULK INSERT'), code('bcp'))),

# 14 upsert
("""PostgreSQL offers %s or %s (the UPSERT pattern), which handles duplicate key scenarios gracefully without aborting the entire batch. SQL Server provides %s for similar upsert semantics, though %s has well-documented edge cases around race conditions and should be used carefully in high-concurrency environments. A safer SQL Server pattern for many upsert scenarios is a targeted %s followed by an %s.""" % (code('INSERT ... ON CONFLICT DO NOTHING'), code('ON CONFLICT DO UPDATE'), code('MERGE'), code('MERGE'), code('UPDATE'), code('INSERT WHERE NOT EXISTS')),
 """SQL Server provides %s for upsert semantics, though %s has well-documented edge cases around race conditions and should be used carefully in high-concurrency environments. A safer pattern for many upsert scenarios is a targeted %s followed by an %s.""" % (code('MERGE'), code('MERGE'), code('UPDATE'), code('INSERT WHERE NOT EXISTS'))),

# 15 pagination
("""Offset-based pagination uses %s and %s (PostgreSQL) or %s (SQL Server).""" % (code('LIMIT'), code('OFFSET'), code('OFFSET FETCH')),
 """Offset-based pagination uses %s in SQL Server.""" % code('OFFSET FETCH')),

# 16 count query
("""using %s or SQL Server's %s for approximate counts,""" % (code('pg_class.reltuples'), code('sys.partitions')),
 """using SQL Server's %s for approximate counts,""" % code('sys.partitions')),

# 17 error codes
("""From the database side, errors come with codes that carry meaning. PostgreSQL uses SQLSTATE codes — a five-character standard inherited from ANSI SQL. SQL Server uses error numbers and severity levels.""",
 """From the database side, errors come with codes that carry meaning. SQL Server uses error numbers and severity levels — capture both in your error handling, because the number identifies the condition and the severity tells you how bad it is."""),

# 18 serialization failure
("""A <strong class="text-white">serialization failure</strong> (SQLSTATE %s in PostgreSQL, which occurs when using %s or %s isolation levels and the transaction conflicts with a concurrent one) is a signal to retry the transaction, not to fail it permanently.""" % (code('40001'), code('REPEATABLE READ'), code('SERIALIZABLE')),
 """A <strong class="text-white">serialization failure</strong> (error 3960 under snapshot isolation, when an update conflicts with a concurrent one) is a signal to retry the transaction, not to fail it permanently."""),

# 19 deadlock
("""A <strong class="text-white">deadlock</strong> (SQLSTATE %s in PostgreSQL, error 1205 in SQL Server) is similar""" % code('40P01'),
 """A <strong class="text-white">deadlock</strong> (error 1205 in SQL Server) is similar"""),

# 20 pool exhaustion
("""If PgBouncer or the ADO.NET pool cannot hand a connection to the caller, the request should be rejected quickly rather than queued indefinitely,""",
 """If the SqlClient pool cannot hand a connection to the caller — all %s connections busy past the connection timeout — the request should be rejected quickly rather than queued indefinitely,""" % code('Max Pool Size')),

# 21 statement timeouts
("""Statement timeouts are an important tool for protecting the database from runaway queries originating from API calls. PostgreSQL's %s can be set at the session, role, or database level. When a query exceeds the timeout, it is terminated with a clear error. SQL Server uses %s or the %s and %s settings at the connection level, and application drivers (JDBC, ADO.NET) typically expose a %s property.""" % (code('statement_timeout'), code('QUERY_GOVERNOR_COST_LIMIT'), code('lock_timeout'), code('query_timeout'), code('CommandTimeout')),
 """Statement timeouts are an important tool for protecting the database from runaway queries originating from API calls. SQL Server's defenses are layered: the driver's %s (SqlClient, JDBC) cancels a runaway command client-side; %s stops estimated-expensive queries before they start; Resource Governor's %s caps execution server-side. Set a command timeout on every API data-access call — an endpoint with no timeout is a runaway query waiting for a bad parameter.""" % (code('CommandTimeout'), code('QUERY_GOVERNOR_COST_LIMIT'), code('REQUEST_MAX_CPU_TIME_SEC'))),

# 22 observability
("""PostgreSQL's %s connection parameter and SQL Server's %s can both carry arbitrary string metadata that appears in the server's activity views.""" % (code('application_name'), code('sp_set_session_context')),
 """SQL Server's %s connection-string keyword and %s carry arbitrary string metadata that appears in the server's activity views.""" % (code('Application Name'), code('sp_set_session_context'))),

# 23 takeaway parameterized
("""but it also introduces parameter sniffing (SQL Server) and generic-vs-custom plan selection (PostgreSQL) as real, intermittent performance failure modes.""",
 """but it also introduces parameter sniffing as a real, intermittent performance failure mode — one query, wildly varying runtimes, same plan hash."""),

# 24 takeaway transactions
("""Transactions held open across external network calls cause lock contention and, in PostgreSQL, block autovacuum; conversely, related writes executed without a transaction at all risk partial failure and real data integrity problems.""",
 """Transactions held open across external network calls cause lock contention and block version-store cleanup under RCSI; conversely, related writes executed without a transaction at all risk partial failure and real data integrity problems."""),
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
    print(f'ch17: all {len(REPLACEMENTS)} replacements applied')

main()
