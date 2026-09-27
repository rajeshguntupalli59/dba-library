#!/usr/bin/env python3
"""Apply ch14 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch14-scaling.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 intro
("""This chapter walks through the full spectrum of scaling techniques available to PostgreSQL and SQL Server DBAs:""",
 """This chapter walks through the full spectrum of scaling techniques available to SQL Server DBAs:"""),

# 2 bottleneck signals
("""Identifying the actual bottleneck requires looking at the right signals. In PostgreSQL, the %s view tells you what sessions are doing right now, and %s exposes how aggressively the background writer is flushing dirty pages — a useful proxy for write I/O pressure. In SQL Server, the %s and %s DMVs are the starting point for almost every performance investigation.""" % (code('pg_stat_activity'), code('pg_stat_bgwriter'), code('sys.dm_exec_requests'), code('sys.dm_os_wait_stats')),
 """Identifying the actual bottleneck requires looking at the right signals. In SQL Server, the %s and %s DMVs are the starting point for almost every performance investigation — the former tells you what sessions are doing right now, the latter tells you what the instance has been waiting on.""" % (code('sys.dm_exec_requests'), code('sys.dm_os_wait_stats'))),

# 3 wait types
(""" In PostgreSQL, %s and %s serve the same diagnostic purpose.""" % (code("wait_event_type = 'Lock'"), code("wait_event_type = 'IO'")),
 """"""),
("""High %s or %s waits in SQL Server point clearly at I/O bottlenecks. High %s waits point at lock contention. The technique you apply to scale the system depends entirely on what you find here.""" % (code('IO_COMPLETION'), code('PAGEIOLATCH_SH'), code('LCK_M_*')),
 """High %s or %s waits point clearly at I/O bottlenecks. High %s waits point at lock contention. The technique you apply to scale the system depends entirely on what you find here.""" % (code('IO_COMPLETION'), code('PAGEIOLATCH_SH'), code('LCK_M_*'))),

# 4 memory buffer pool
("""both PostgreSQL and SQL Server maintain an in-memory buffer pool, and the fraction of your working data set that fits in that pool determines how often the system reads from disk versus from memory.""",
 """SQL Server maintains an in-memory buffer pool, and the fraction of your working data set that fits in that pool determines how often the system reads from disk versus from memory."""),

# 5 memory settings
("""In PostgreSQL, the %s parameter controls the size of the shared buffer cache. A common starting point is 25%% of total RAM, though on dedicated database servers with large working sets this can go higher. The %s parameter does not allocate memory itself — it informs the query planner about total memory available for caching (including the OS page cache), and setting it accurately to around 75%% of total RAM helps the planner prefer index scans over sequential scans on large tables. In SQL Server, the %s setting controls the buffer pool ceiling. On a dedicated server, you set this to total RAM minus a reserve for the OS and other processes — typically leaving 10-20%% or at least 4GB for the OS on smaller servers.""" % (code('shared_buffers'), code('effective_cache_size'), code('max server memory')),
 """In SQL Server, the %s setting controls the buffer pool ceiling. On a dedicated server, set this to total RAM minus a reserve for the OS and other processes — typically leaving 10-20%% or at least 4GB for the OS on smaller servers. Under-sizing max server memory is the most common memory misconfiguration: SQL Server will use what you give it, and an undersized buffer pool turns a memory-fit workload into a disk-bound one. Watch Page Life Expectancy — a value persistently under 300 seconds on OLTP means the buffer pool is under pressure.""" % code('max server memory')),

# 6 parallelism
("""CPU scaling matters most for analytical workloads. Both engines support intra-query parallelism, where a single query executes across multiple CPU cores simultaneously. In PostgreSQL, %s controls how many parallel workers a single query can use, and %s and %s influence when the planner chooses a parallel plan. In SQL Server, the %s (MAXDOP) server configuration sets an upper bound, and the %s setting determines how expensive a serial plan must be before parallelism is considered.""" % (code('max_parallel_workers_per_gather'), code('parallel_tuple_cost'), code('parallel_setup_cost'), code('max degree of parallelism'), code('cost threshold for parallelism')),
 """CPU scaling matters most for analytical workloads. SQL Server supports intra-query parallelism, where a single query executes across multiple CPU cores simultaneously. The %s (MAXDOP) server configuration sets an upper bound, and the %s setting determines how expensive a serial plan must be before parallelism is considered.""" % (code('max degree of parallelism'), code('cost threshold for parallelism'))),

# 7 storage log
("""Placing the write-ahead log (WAL) in PostgreSQL or the transaction log file in SQL Server on dedicated, high-throughput storage is a simple and effective technique.""",
 """Placing the transaction log file on dedicated, high-throughput storage is a simple and effective technique — log writes are sequential, so they benefit enormously from isolated, low-latency devices."""),

# 8 partitioning maintenance
("""It is primarily a manageability and performance technique for large tables, and it becomes relevant when a table has grown to the point where maintenance operations (VACUUM, index rebuilds) are slow, queries are scanning more data than they need to, and archiving old data requires deleting from a table that is always hot.""",
 """It is primarily a manageability and performance technique for large tables, and it becomes relevant when a table has grown to the point where maintenance operations (index rebuilds, CHECKDB) are slow, queries are scanning more data than they need to, and archiving old data requires deleting from a table that is always hot."""),

# 9 global/local indexes
("""and understand how global indexes and local indexes behave differently across the two platforms.""",
 """and understand how aligned and non-aligned indexes behave differently — partition-aligned indexes switch partitions in metadata-only operations, non-aligned ones don't."""),

# 10 mermaid pooler
("""Pooler["Connection Pooler\\n(PgBouncer / AG Listener)"]""",
 """Pooler["Connection Pooler\\n(ADO.NET pooling / AG Listener)"]"""),

# 11 PG streaming replication -> AG secondaries
("""PostgreSQL implements streaming replication using the write-ahead log. The primary writes WAL records, and standbys stream and apply those records continuously, typically with a lag of milliseconds on a healthy network. Standbys can be configured as hot standby, meaning they accept read-only connections while replication is running. You can promote a standby to primary for failover. PostgreSQL also supports logical replication, which replicates at the row change level rather than the physical WAL level, allowing selective replication of specific tables and compatibility between different PostgreSQL major versions.""",
 """SQL Server implements read scale-out through Availability Group secondary replicas. The primary streams transaction-log records to secondaries continuously, typically with a lag of milliseconds on a healthy network. Secondaries can be readable, accepting read-only connections while redo runs — with %s routing through the AG listener sending reporting traffic there automatically. For simpler needs, log shipping provides a delayed standby without the AG infrastructure.""" % code('ApplicationIntent=ReadOnly')),

# 12 app-side routing
("""Application-side routing to replicas can be implemented at several layers: in the application's connection pool configuration (many frameworks support primary/replica connection strings natively), in a connection pooler like PgBouncer with appropriate routing logic, or in a proxy layer like ProxySQL for MySQL-compatible workloads or HAProxy configured to forward read traffic to replica nodes. SQL Server's Always On listener provides a single virtual network name that routes connections to the appropriate replica based on the %s property in the connection string, which is a clean and low-friction approach.""" % code('ApplicationIntent'),
 """Application-side routing to replicas can be implemented at several layers: in the application's connection configuration (many frameworks support primary/replica connection strings natively), or through SQL Server's Always On listener, which provides a single virtual network name routing connections to the appropriate replica based on the %s property in the connection string — a clean, low-friction approach.""" % code('ApplicationIntent')),

# 13 sharding/Citus
("""Beyond read replicas, some workloads eventually require sharding — distributing writes across multiple nodes by partitioning the data itself. PostgreSQL's Citus extension, available as a managed service in Azure Database for PostgreSQL, distributes tables across worker nodes and parallelizes queries across shards. This is a significant architectural commitment and is appropriate for workloads that have genuinely outgrown a single primary node's write capacity, which is a relatively high threshold that most systems never reach. SQL Server Elastic Database features in Azure SQL offer similar capabilities for cloud-based workloads. Both approaches require careful selection of a distribution key that prevents hot shards and allows most queries to be resolved on a single node rather than requiring cross-shard scatter-gather execution.""",
 """Beyond read replicas, some workloads eventually require sharding — distributing writes across multiple nodes by partitioning the data itself. The honest guidance: you probably don't need it. A single well-tuned primary handles enormous write throughput, and most systems never reach its limit. For Azure SQL, Elastic Database features (elastic pools for multi-tenant scale, shard maps for distribution) offer the path when you genuinely outgrow one primary. Sharding is a significant architectural commitment — it requires careful selection of a distribution key that prevents hot shards and allows most queries to be resolved on a single node rather than requiring cross-shard scatter-gather execution."""),

# 14 connection limits
("""One of the most consistently underestimated scaling challenges is connection management. Both PostgreSQL and SQL Server have hard limits on concurrent connections, and both suffer meaningful performance degradation well before those limits are reached. Understanding this problem and the tools that solve it is non-negotiable knowledge for any production DBA.""",
 """One of the most consistently underestimated scaling challenges is connection management. SQL Server's configurable connection limit is high, but throughput degrades well before it — worker-thread exhaustion and scheduler contention bite long before you hit any configured ceiling. Understanding this problem and the tools that solve it is non-negotiable knowledge for any production DBA."""),

# 15 PG process model -> thread pool
("""In PostgreSQL, each connection corresponds to a separate OS process. At 100 connections, memory overhead is modest. At 500 connections, you are consuming gigabytes of process memory even when those connections are idle. At 1000+ connections, context switching overhead and lock manager data structure contention begin to visibly degrade throughput, even on hardware with plenty of available CPU. The %s parameter in %s caps the total, and the default of 100 is intentionally conservative — not because the system cannot open more sockets, but because many concurrent connections degrade rather than improve throughput under load.""" % (code('max_connections'), code('postgresql.conf')),
 """In SQL Server, each connection gets a worker thread from the thread pool. Hundreds of connections are fine; thousands of concurrently active connections cause worker-thread exhaustion and scheduler contention that visibly degrade throughput, even on strong hardware. The practical guidance is the same as everywhere: far fewer active connections than you think, with pooling in front — and monitor %s for the workers actually in use.""" % code('sys.dm_os_workers')),

# 16 PgBouncer -> ADO.NET pooling
("""The standard solution is a connection pooler that sits between the application and the database. Applications connect to the pooler, which maintains a smaller set of long-lived connections to the database. The pooler multiplexes many short-lived application connections onto fewer database connections. For PostgreSQL, <strong class="text-white">PgBouncer</strong> is the dominant choice, operating in one of three modes: session pooling (one database connection per application session, held for the session's lifetime), transaction pooling (a database connection is checked out only for the duration of a transaction, then returned to the pool), and statement pooling (a connection is held only for a single statement). Transaction pooling is the most effective at reducing connection count but is incompatible with features that depend on session-level state — prepared statements in their native form, advisory locks held between transactions, and %s commands that modify session parameters.""" % code('SET'),
 """The standard solution is connection pooling. In the SQL Server world this lives primarily in the client driver: <strong class="text-white">ADO.NET / SqlClient pooling</strong> maintains a pool of long-lived connections per connection string, multiplexing application open/close calls onto fewer real database connections. The pool is keyed by the exact connection string — which is why the guidance is to use identical connection strings everywhere and never build them dynamically per user. ODBC and JDBC drivers pool similarly; a middle-tier pooler (or the application's own pool) sits between app and database doing the same multiplexing job. Pooling breaks down the moment session-level state matters — temp tables, SET options, and open transactions pin a connection to its session, so keep pooled work stateless and short."""),

# 17 idle timeouts
("""Idle connection timeouts deserve attention on both platforms. In PostgreSQL, %s is an underused but important parameter. When a connection holds a transaction open without executing queries — usually because of a bug or network interruption — it holds locks that block other sessions. Setting this parameter to something reasonable (30 seconds to a few minutes, depending on workload) automatically terminates those connections and releases their locks. SQL Server has no direct equivalent server-side timeout for idle transactions, making application-level timeout handling more important.""" % code('idle_in_transaction_session_timeout'),
 """Idle connection handling deserves attention. SQL Server has no server-side timeout for idle open transactions, which makes application-level timeout handling critical: a leaked transaction holds locks indefinitely and blocks version-store cleanup under RCSI. Set command timeouts in the data-access layer, audit for sessions with open transactions and no active request, and treat connection leaks as bugs to fix rather than tuning opportunities."""),

# 18 CQRS materialized views
("""In PostgreSQL, materialized views serve a similar purpose within the database itself and can be refreshed on a schedule or triggered by data changes.""",
 """In SQL Server, indexed views serve a similar purpose within the database itself — materialized and maintained automatically by the engine, at the cost of write overhead on the base tables."""),

# 19 workload isolation
("""PostgreSQL's Resource Groups (available through extensions and in some managed services) and SQL Server's Resource Governor allow you to cap CPU and memory allocations per workload group, ensuring that an analyst running a large report cannot starve transactional sessions of resources.""",
 """SQL Server's Resource Governor allows you to cap CPU and memory allocations per workload group, ensuring that an analyst running a large report cannot starve transactional sessions of resources."""),

# 20 physical separation
("""Where a true built-in resource governor is not available or not configured, the simpler and more common pattern on both platforms is physical separation: route analytical and reporting workloads to a read replica, and reserve the primary exclusively for transactional traffic.""",
 """Where Resource Governor isn't configured, the simpler and more common pattern is physical separation: route analytical and reporting workloads to a read replica, and reserve the primary exclusively for transactional traffic."""),

# 21 takeaway diagnose
("""CPU, memory, I/O, and connection pressure each have distinct signatures in `pg_stat_activity`/`pg_stat_bgwriter` and `sys.dm_exec_requests`/`sys.dm_os_wait_stats`; scaling the wrong resource wastes money and doesn't fix the actual bottleneck. Optimize first — scaling inefficient queries just runs them on more expensive hardware.""",
 """CPU, memory, I/O, and connection pressure each have distinct signatures in `sys.dm_exec_requests` and `sys.dm_os_wait_stats`; scaling the wrong resource wastes money and doesn't fix the actual bottleneck. Optimize first — scaling inefficient queries just runs them on more expensive hardware."""),

# 22 takeaway sharding
("""horizontal write scaling (sharding via Citus or Elastic Database) is a significant architectural commitment appropriate only once a single primary's write capacity is genuinely insufficient.""",
 """horizontal write scaling (sharding via Elastic Database) is a significant architectural commitment appropriate only once a single primary's write capacity is genuinely insufficient — a threshold most systems never reach."""),

# 23 takeaway pooling
("""**Connection pooling is not optional at scale.** Both PostgreSQL's process-per-connection model and SQL Server's thread-pool model degrade well before their hard connection limits; PgBouncer, driver-level pooling, and idle transaction timeouts are standard production requirements, not advanced tuning.""",
 """**Connection pooling is not optional at scale.** SQL Server's thread-pool model degrades well before hard connection limits; driver-level pooling (ADO.NET/SqlClient), identical connection strings, and application command timeouts are standard production requirements, not advanced tuning."""),
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
    print(f'ch14: all {len(REPLACEMENTS)} replacements applied')

main()
