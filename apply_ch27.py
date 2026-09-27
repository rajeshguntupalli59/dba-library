#!/usr/bin/env python3
"""Apply ch27 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch27-microservices.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 intro
("""This chapter covers what microservices mean for database operations, how PostgreSQL and SQL Server fit into that ecosystem, and the production-level patterns that keep data consistent and performant when your architecture is deliberately distributed.""",
 """This chapter covers what microservices mean for database operations, how SQL Server fits into that ecosystem, and the production-level patterns that keep data consistent and performant when your architecture is deliberately distributed."""),

# 2 per-service model
("""PostgreSQL handles this model well because it is lightweight enough to run as a dedicated instance per service, either in containers or on smaller virtual machines. SQL Server historically was heavier and more expensive to run at this granularity, though SQL Server on Linux and Azure SQL Database have made the economics more reasonable. In practice, many organizations using SQL Server compromise with a *schema per service* approach inside a shared instance, rather than a fully separate database per service — a pattern worth understanding for both its convenience and its risks.""",
 """SQL Server fits this model at several granularities. The database-per-service ideal maps naturally to one database per service — on a shared instance, on SQL Server containers in Kubernetes, or as separate Azure SQL databases. Many organizations compromise with a *schema per service* approach inside a shared database instead: convenient for cross-service queries and connection efficiency, but with real noisy-neighbor and blast-radius risks — one service's runaway query or schema lock affects everyone in the database. Whatever granularity you choose, make it a deliberate decision with ownership boundaries, not an accident of convenience."""),

# 3 connection overhead
("""PostgreSQL's connection overhead is significant. Each connection spawns a backend process, consuming memory — typically two to five megabytes per connection at idle, more under load. A PostgreSQL instance accepting five hundred direct connections from microservice pods can exhaust memory before it processes a single query. This is why PgBouncer, the connection pooler for PostgreSQL, becomes nearly mandatory in microservices environments.""",
 """Connection math gets dangerous fast in microservices. Fifty pods per service times twenty services times ten connections per pod is ten thousand connections — and while a SQL Server connection is lighter than a process-per-connection design, ten thousand of them still means serious memory and scheduler pressure. SqlClient connection pooling in each service process is the baseline defense: the pool amortizes connection setup and bounds the per-process count with %s, so the database sees hundreds of connections instead of thousands.""" % code('Max Pool Size')),

# 4 PgBouncer
("""PgBouncer sits between the service pods and the PostgreSQL instance. Services connect to PgBouncer, which maintains a smaller pool of actual database connections. In transaction pooling mode, a database connection is held only for the duration of a transaction, then returned to the pool. This allows hundreds of application connections to share a much smaller number of real database connections. The tradeoff is that session-level state — prepared statements, temporary tables, advisory locks — does not survive across transactions when the connection is shared, which catches teams off guard when they migrate from a direct-connection model.""",
 """There is no PgBouncer tier for SQL Server — the driver pools, per process. That removes a moving part but creates its own gotchas. The pool is keyed by the exact connection string, so per-pod configuration drift (a different timeout here, an extra parameter there) silently fragments one logical pool into many small ones. And while %s cleans session state between checkouts, temporary tables created in a pooled session survive the checkout — a service that creates temp tables and doesn't drop them will eventually collide with itself on the next checkout of that connection.""" % code('sp_reset_connection')),

# 5 nullable columns
("""Both PostgreSQL and SQL Server support adding nullable columns to large tables without a full table lock in modern versions, which makes the expand phase operationally safe. However, adding a NOT NULL column without a default requires a full table rewrite in older PostgreSQL versions — in PostgreSQL 11 and later, adding a column with a non-null default no longer rewrites the table, which was a significant improvement for microservices teams.""",
 """SQL Server supports adding nullable columns to large tables as a metadata-only operation, which makes the expand phase operationally safe — and since SQL Server 2012, adding a NOT NULL column *with* a default is metadata-only too. The dangerous case is adding a NOT NULL column without a default on a populated table, which rewrites every row. In a schema-per-service database, coordinate even "safe" DDL: a metadata lock is brief, but on a hot table brief is all it takes to pile up blocked sessions."""),

# 6 index concurrently
("""The %s in PostgreSQL and %s in SQL Server are both ways to build indexes without blocking reads and writes — essential when services are always running and a maintenance window is not an option.""" % (code('CREATE INDEX CONCURRENTLY'), code('WITH (ONLINE = ON)')),
 """%s builds indexes without blocking reads and writes — essential when services are always running and a maintenance window is not an option. Online builds still take locks at the start and end, so on very hot tables expect brief blocking; for multi-terabyte tables, consider resumable index builds (%s) so a killed build doesn't start over.""" % (code('CREATE INDEX ... WITH (ONLINE = ON)'), code('RESUMABLE = ON'))),

# 7 outbox
("""The outbox table needs to be polled or streamed efficiently. In PostgreSQL, logical replication and Debezium can stream outbox rows as change events without a polling loop, which reduces latency significantly. In SQL Server, SQL Server Change Data Capture (CDC) or the transactional replication publication mechanism can serve the same purpose.""",
 """The outbox table needs to be polled or streamed efficiently. SQL Server Change Data Capture (CDC) can stream outbox rows as change events without a polling loop, which reduces latency significantly; where CDC is too heavy, a relay polling with %s stays efficient and lets multiple relay instances share the work.""" % code('WITH (UPDLOCK, READPAST)')),

# 8 app name
("""The first tool is application-level labeling. Both PostgreSQL and SQL Server support application-level connection properties that show up in monitoring views. Developers should set the application name on every connection to include the service name and ideally the service version. In PostgreSQL, this appears in %s. In SQL Server, it shows up in %s.""" % (code('pg_stat_activity.application_name'), code('sys.dm_exec_sessions.program_name')),
 """The first tool is application-level labeling. The %s connection property shows up in %s — developers should set it on every connection to include the service name and ideally the service version. When twenty services share an instance, program_name is how you tell whose query is burning the CPU.""" % (code('Application Name'), code('sys.dm_exec_sessions.program_name'))),

# 9 auto_explain
("""Auto-explain in PostgreSQL (via the %s extension) can log the execution plan of any query that exceeds a configurable duration threshold, writing the output to the server log. Combined with trace context in comments, a DBA can look at a slow plan and know exactly which service version on which endpoint triggered it.""" % code('auto_explain'),
 """SQL Server's Query Store captures plans and wait statistics per query automatically. Combined with trace context in comments and the application-name labeling above, a DBA can look at a regressed plan and know exactly which service version on which endpoint triggered it — and force the good plan back while the service team fixes the query."""),

# 10 PVC
("""The core concern with stateful containers is data persistence. A container is ephemeral by default — if it restarts, the filesystem is gone. Both PostgreSQL and SQL Server running in Kubernetes require a *Persistent Volume Claim* (PVC) backed by durable storage. The choice of storage class matters: network-attached storage (NAS or AWS EFS) introduces latency that heavily impacts write-intensive databases. Local NVMe-backed persistent volumes on the node give much better performance but come with the constraint that the pod must schedule on the specific node where the volume lives.""",
 """The core concern with stateful containers is data persistence. A container is ephemeral by default — if it restarts, the filesystem is gone. SQL Server running in Kubernetes requires a *Persistent Volume Claim* (PVC) backed by durable storage. The choice of storage class matters: network-attached storage introduces latency that heavily impacts write-intensive databases. Local NVMe-backed persistent volumes on the node give much better performance but come with the constraint that the pod must schedule on the specific node where the volume lives — which fights the scheduler's desire to move things around."""),

# 11 operators
("""PostgreSQL is well-supported in Kubernetes through operators — CloudNativePG and Crunchy Data PGO are the most production-ready. These operators handle streaming replication setup, automated failover, connection pooling via PgBouncer sidecar, scheduled backups to object storage (S3, GCS), and rolling restarts that respect replication lag before proceeding. For a team running microservices on Kubernetes, a PostgreSQL operator removes the manual operational burden that would otherwise require deep DBA involvement in every cluster provisioning event.""",
 """SQL Server on Kubernetes runs as StatefulSets with PVC-backed storage, but there is no dominant production operator equivalent to manage the lifecycle — no built-in automated failover, no backup scheduling, no replication-lag-aware rolling restarts. Availability groups on Kubernetes are technically possible and operationally heavy (the cluster quorum story gets interesting when nodes are cattle). Most teams choose one of two sane paths: containerized SQL Server for stateless-ish or dev/test workloads with the database files on durable PVCs, or managed offerings (Azure SQL Database, Managed Instance) for anything production that needs real HA. Don't build your own operator unless operating databases on Kubernetes is your product."""),

# 12 resource limits
("""Resource limits in Kubernetes are another area the DBA must influence. If a container's memory limit is set lower than PostgreSQL's """ + code('shared_buffers') + """ plus working memory, the container will be OOM-killed under load. A DBA reviewing Kubernetes manifests for a database container should verify that """ + code('shared_buffers') + """ is set to roughly 25% of the container's memory limit, that """ + code('work_mem') + """ is not set so high that concurrent sort operations exhaust available memory, and that """ + code('max_connections') + """ is configured in concert with the PgBouncer pool size.""",

"""Resource limits in Kubernetes are another area the DBA must influence. If a container's memory limit is set lower than %s plus OS headroom, the container will be OOM-killed under load \u2014 and SQL Server, which happily grows to its configured max, will find that limit fast. A DBA reviewing Kubernetes manifests for a database container should verify that %s is set well under the container's memory limit, and that each service's %s values are sized against the fleet total, not just the single pod.""" % (code('max server memory'), code('max server memory'), code('Max Pool Size'))),

# 13 backups
("""Backup strategy in Kubernetes requires deliberate planning. The assumption that a DBA manually triggers %s or SQL Server backups on a schedule does not hold when pods are ephemeral and the backup tooling needs to live alongside the data. Operators that schedule continuous WAL archiving to S3 (for PostgreSQL) or transaction log shipping to Azure Blob Storage (for SQL Server) give you point-in-time recovery without relying on a human being physically present to initiate the backup.""" % code('pg_dump'),
 """Backup strategy in Kubernetes requires deliberate planning. The assumption that a DBA manually triggers backups on a schedule does not hold when pods are ephemeral. Schedule native backups to URL — full, differential, and transaction log to Azure Blob Storage — from an Agent job or a CronJob that targets the SQL Server pod; that gives you point-in-time recovery without relying on a human being present to initiate the backup, and the backups survive the pod."""),

# 14 takeaway pooling
("""Connection pooling is not optional at microservices scale; PgBouncer for PostgreSQL and properly sized connection pools per SQL Server service account are the operational baseline for keeping connection counts sane under pod-based deployment.""",
 """Connection pooling is not optional at microservices scale; properly sized SqlClient pools per service are the operational baseline for keeping connection counts sane under pod-based deployment."""),

# 15 takeaway observability
("""Observability in a distributed system requires the DBA to invest in application-name labeling, trace context in SQL comments, and tools like PostgreSQL's `auto_explain` and SQL Server's Query Store to correlate slow queries back to the specific service, version, and request path that triggered them.""",
 """Observability in a distributed system requires the DBA to invest in application-name labeling, trace context in SQL comments, and SQL Server's Query Store to correlate slow queries back to the specific service, version, and request path that triggered them."""),
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
    print(f'ch27: all {len(REPLACEMENTS)} replacements applied')

main()
