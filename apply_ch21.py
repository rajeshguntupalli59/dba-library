#!/usr/bin/env python3
"""Apply ch21 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch21-advanced-architecture.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
P = '<p class="text-gray-300 leading-relaxed">'
LI = '<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> %s</li>'

POOLER_SUBSECTION = (
P + "<strong class=\"text-white\">SqlClient connection pooling</strong> is the standard pooling mechanism for SQL Server, and it lives in the driver rather than as an external tier. The pool is keyed by the exact connection string: " + code('Open()') + " checks out a pooled connection, " + code('Close()') + "/" + code('Dispose') + " returns it, and the driver issues " + code('sp_reset_connection') + " to clean session state between checkouts. The knobs that matter:</p>\n\n" +
LI % ("<strong class=\"text-white\">Min Pool Size / Max Pool Size</strong>: the floor the pool keeps warm and the ceiling per application process. Size the ceiling from measured concurrency across your whole app fleet — 50 app servers × 100 is 5,000 database connections.") + "\n" +
LI % ("<strong class=\"text-white\">Connection Lifetime</strong>: how long a pooled connection lives before being recycled; recycling bounds the damage from leaked session state.") + "\n" +
LI % ("<strong class=\"text-white\">Identical connection strings</strong>: any difference — even whitespace — creates a separate pool. Build connection strings once, centrally, never per user or per request.") + "\n\n" +
P + "The catch mirrors every pooler: pooled connections must be stateless. Temp tables, session SET options, and open transactions don't reliably survive a checkout — " + code('sp_reset_connection') + " clears most of it, and anything it misses becomes an intermittent bug. Keep pooled work short and stateless, and never hold a pooled connection across user think time.</p>"
)

REPLACEMENTS = [
# 1 partitioning intro
("""Partitioning primarily solves performance problems — queries that touch only recent data don't scan years of history, and maintenance operations like archival and vacuuming can target individual partitions. Both PostgreSQL and SQL Server have mature declarative partitioning support.""",
 """Partitioning primarily solves performance problems — queries that touch only recent data don't scan years of history, and maintenance operations like archival and index rebuilds can target individual partitions. SQL Server's declarative partitioning (partition functions and schemes) is mature and production-proven."""),

# 2 PG partitioning syntax
("""PostgreSQL's native table partitioning uses the %s syntax introduced in version 10 and matured significantly in versions 11–14. SQL Server's equivalent is the partition function and partition scheme model, which maps ranges to filegroups.""" % code('CREATE TABLE ... PARTITION BY'),
 """SQL Server's partitioning model uses a partition function (mapping ranges to partition numbers) and a partition scheme (mapping partitions to filegroups). Partition-aligned indexes let you switch partitions in and out as metadata-only operations — the workhorse pattern for sliding-window archival of time-series data."""),

# 3 read replicas
("""<strong class="text-white">Physical read replicas</strong> are the simplest form. The application routes all writes to the primary and all reads to one or more replicas. PostgreSQL's streaming replication and SQL Server's Always On Availability Groups both support this pattern. The tradeoff is replication lag — a replica might be a few milliseconds to several seconds behind the primary, so reads that require the absolute latest data must still go to the primary.""",
 """<strong class="text-white">Physical read replicas</strong> are the simplest form. The application routes all writes to the primary and all reads to one or more replicas. SQL Server's Always On Availability Groups support this pattern, with readable secondaries taking the read load via %s routing. The tradeoff is replication lag — a secondary might be milliseconds to seconds behind the primary, so reads that require the absolute latest data must still go to the primary.""" % code('ApplicationIntent=ReadOnly')),

# 4 PG CDC
("""PostgreSQL implements CDC through its logical replication system. Logical replication slots expose the write-ahead log (WAL) as a decoded stream of row-level changes. Tools like Debezium consume this stream and publish to Kafka, from which any number of consumers can read independently at their own pace.""",
 """SQL Server implements CDC by reading the transaction log: the capture job harvests row changes into change tables, one per tracked table. ETL jobs poll the change tables, or Debezium's SQL Server connector streams them into Kafka, from which any number of consumers can read independently at their own pace."""),

# 5 CDC backpressure
("""In PostgreSQL, an inactive logical replication slot will cause WAL to accumulate until the disk fills up — a silent, creeping disaster. Monitoring slot lag is non-negotiable in any CDC deployment. In SQL Server, the CDC cleanup jobs handle retention automatically, but you need to verify those jobs are running and that their retention window matches your consumers' recovery time expectations.""",
 """An unconsumed change feed will cause the change tables to grow until the disk fills up — a silent, creeping disaster. The CDC cleanup jobs handle retention automatically, but you need to verify those jobs are running and that their retention window matches your consumers' recovery time expectations. Monitor capture latency as the primary health signal of the whole pipeline."""),

# 6 active-passive
("""This is the most common pattern for OLTP databases because it preserves strong consistency during normal operations. PostgreSQL's streaming replication and SQL Server's Always On Availability Groups both implement this pattern well.""",
 """This is the most common pattern for OLTP databases because it preserves strong consistency during normal operations. Always On Availability Groups implement it well, with automatic failover inside a cluster and manual or forced failover across regions."""),

# 7 active-active
("""PostgreSQL doesn't natively support multi-master replication; tools like BDR (Bi-Directional Replication) from EDB provide it as an extension. SQL Server has no native multi-master either, though some architectures use distributed availability groups with conflict-avoidance through shard-per-region.""",
 """SQL Server has no native multi-master: the supported patterns are conflict-avoidance designs — shard-per-region (each region owns its writes), or distributed availability groups with a single global primary. True active-active with conflict resolution belongs in the application layer, not the database."""),

# 8 failover connections
("""PgBouncer in front of PostgreSQL and SQL Server's transparent network name (via Windows Server Failover Clustering or the AG listener) both abstract the connection endpoint so applications don't need to know which server is currently primary.""",
 """SQL Server's AG listener abstracts the connection endpoint — a single virtual network name that always resolves to the current primary — so applications don't need to know which server holds the role. Pair it with retry logic: during failover, in-flight connections break and pools must drain and reconnect."""),

# 9 connection resources
("""Every database connection consumes real resources. PostgreSQL forks a backend process per connection; a connection that's idle still holds memory, file descriptors, and a slot in the shared memory structures. SQL Server's thread model is more efficient, but connections still consume memory and worker threads. At scale, the number of application instances multiplied by the number of threads per instance quickly exceeds what a database can handle directly.""",
 """Every database connection consumes real resources. SQL Server assigns a worker thread per connection — an idle connection still holds memory and a thread, and thousands of active connections cause scheduler contention. At scale, the number of application instances multiplied by the threads per instance quickly exceeds what a database can handle directly, which is why pooling is architectural, not optional."""),

# 12 middle-tier pooler
("""SQL Server doesn't need an external pooler the same way PostgreSQL does because SQL Server's connection model is more efficient and its client libraries (ADO.NET, JDBC, ODBC) implement connection pooling in-process. However, at very high scale or in environments with hundreds of microservices, external poolers or PgBouncer-style middleware become relevant for SQL Server too.""",
 """SQL Server doesn't need an external pooler tier because the driver pools in-process — but at very high scale, with hundreds of microservices, a centralized middle-tier pool becomes relevant to cap total database connections. The AG listener with %s routing covers the read/write split; the middle tier covers connection-count fan-in.""" % code('ApplicationIntent')),

# 13 where to deploy
("""The architectural question that matters most is where to deploy the connection pooler. Deploying PgBouncer on the same host as the database eliminates network overhead between pooler and database but creates a single point of failure. Deploying it on a separate set of hosts (typically 2–3 pooler nodes behind a load balancer) is more resilient but adds a network hop. In Kubernetes environments, a PgBouncer sidecar per application pod is increasingly common, but this defeats the pooling purpose for the database — you want the pooler close to the database, not distributed across application pods.""",
 """The architectural question that matters most is where pooling lives. Driver-level pooling is per process — simple, no extra tier, but the database sees the sum of every app server's pool. A middle-tier pool consolidates that fan-in at the cost of another component to operate and a network hop. In Kubernetes environments, a sidecar pooler per application pod is increasingly common, but this defeats the purpose for the database — you want pooling consolidated close to the database, not fragmented across pods."""),

# 14 sizing
("""Sizing the pool correctly requires understanding your workload. The rule of thumb for PostgreSQL — rooted in research and widely tested in production — is that the optimal number of active database connections is approximately %s. Beyond that number, connections queue behind each other and throughput actually decreases due to lock contention and context switching. A 32-core server with fast NVMe storage might perform optimally at 70 active connections, even if it could technically accept 500. PgBouncer's %s handles the overflow by queuing client connections, which is far cheaper than having 500 active backend processes.""" % (code('2 × num_cores + num_disks'), code('max_client_conn')),
 """Sizing the pool correctly requires understanding your workload. The rule of thumb — rooted in research and widely tested in production — is that the optimal number of active database connections is approximately %s. Beyond that number, connections queue behind each other and throughput actually decreases due to lock contention and context switching. A 32-core server with fast NVMe storage might perform optimally at 70 active connections even if it could technically accept 500. Size %s so the fleet's total stays near that optimum — queuing in the pool is far cheaper than 500 active workers fighting over schedulers.""" % (code('2 × num_cores + num_disks'), code('Max Pool Size'))),

# 15 metrics
("""Prometheus with postgres_exporter is the standard open-source stack for PostgreSQL metrics. SQL Server ships with its own DMV-based metrics infrastructure that integrates naturally with SQL Server Management Studio, Azure Monitor, and third-party tools like Datadog or SolarWinds.""",
 """SQL Server ships with a DMV-based metrics infrastructure (%s and friends) that integrates naturally with SQL Server Management Studio, Azure Monitor, and third-party tools like Datadog or SolarWinds; Prometheus exporters exist for shops standardizing on that stack.""" % code('sys.dm_os_performance_counters')),

# 16 logs
("""<strong class="text-white">Logs</strong> tell you what happened in narrative form. Slow query logs, error logs, connection logs, autovacuum logs — these are discrete events with context you can query after the fact.""",
 """<strong class="text-white">Logs</strong> tell you what happened in narrative form. Error logs, XEvent captures, Query Store history, Agent job history — these are discrete events with context you can query after the fact."""),

# 17 takeaway CDC
("""**CDC and event sourcing make your database a first-class event producer**: logical replication slots in PostgreSQL and CDC tables in SQL Server give downstream systems a reliable change stream, but both require active monitoring for consumer lag to avoid runaway WAL or log retention.""",
 """**CDC and event sourcing make your database a first-class event producer**: CDC change tables give downstream systems a reliable change stream, but they require active monitoring of capture latency and cleanup-job health to avoid runaway change-table growth."""),
]

def main():
    text = open(PATH).read()
    # Replace PgBouncer subsection (header para through transaction-mode para) with SqlClient pooling.
    idx_a = text.index('<strong class="text-white">PgBouncer</strong> is the standard external connection pooler')
    idx_b = text.index("SQL Server doesn't need an external pooler")
    start = text.rindex('<p class="text-gray-300 leading-relaxed">', 0, idx_a)
    end = text.rindex('<p class="text-gray-300 leading-relaxed">', 0, idx_b)
    text = text[:start] + POOLER_SUBSECTION + '\n\n' + text[end:]
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch21: subsection replaced + all {len(REPLACEMENTS)} replacements applied')

main()
