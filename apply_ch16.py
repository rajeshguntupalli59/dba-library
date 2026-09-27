#!/usr/bin/env python3
"""Apply ch16 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch16-integrations.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

POOLING_CONNSTR = """<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>Server=tcp:sqlprod01.corp.local,1433;Database=appdb;
User ID=app_svc;Password=...;Encrypt=True;TrustServerCertificate=False;
Min Pool Size=5;Max Pool Size=100;Connection Timeout=30;
Connection Lifetime=600;Application Name=OrderService;</code></pre>"""

REPLACEMENTS = [
# 1 intro
("""In modern production environments, PostgreSQL and SQL Server must speak to application servers, message queues, ETL pipelines, cloud platforms, reporting tools, and sometimes each other.""",
 """In modern production environments, SQL Server must speak to application servers, message queues, ETL pipelines, cloud platforms, reporting tools, and data warehouses."""),
("""from application connectivity and connection pooling, to foreign data wrappers, linked servers, ETL pipelines, and event-driven architectures.""",
 """from application connectivity and connection pooling, to linked servers, ETL pipelines, and event-driven architectures."""),

# 2 driver ecosystem
("""Both PostgreSQL and SQL Server have mature driver ecosystems, but the choices you make at the driver level ripple through everything above it — query performance, connection handling, error recovery, and security.""",
 """SQL Server has a mature driver ecosystem, but the choices you make at the driver level ripple through everything above it — query performance, connection handling, error recovery, and security."""),

# 3 drivers paragraph
("""For PostgreSQL, the most common drivers are <strong class="text-white">libpq</strong> (the native C library that most other drivers wrap), <strong class="text-white">psycopg2</strong> and <strong class="text-white">psycopg3</strong> for Python, <strong class="text-white">pgx</strong> for Go, <strong class="text-white">node-postgres</strong> for Node.js, and <strong class="text-white">JDBC with the official PostgreSQL JDBC driver</strong> for JVM languages. For SQL Server, the primary options are the <strong class="text-white">Microsoft JDBC Driver</strong>, <strong class="text-white">pyodbc</strong> or <strong class="text-white">pymssql</strong> for Python, the <strong class="text-white">SqlClient</strong> library for .NET, and <strong class="text-white">Go's %s with the mssql driver</strong>.""" % code('database/sql'),
 """For SQL Server, the primary options are the <strong class="text-white">SqlClient</strong> library for .NET, the <strong class="text-white">Microsoft JDBC Driver</strong> for JVM languages, <strong class="text-white">pyodbc</strong> for Python, <strong class="text-white">node-mssql</strong> for Node.js, and <strong class="text-white">Go's %s with the mssql driver</strong>. Prefer Microsoft's first-party drivers: they track new SQL Server features (Always Encrypted, Azure AD authentication, UTF-8 support) fastest and carry the pooling and retry behavior this chapter describes.""" % code('database/sql')),

# 4 connection strings
("""production connection strings often also encode SSL requirements, connection timeouts, application names, and target session attributes (for PostgreSQL read replicas). The application name parameter deserves special attention — it shows up in %s and SQL Server's %s, making it far easier to identify which service is responsible for a problematic query.""" % (code('pg_stat_activity'), code('sys.dm_exec_sessions')),
 """production connection strings often also encode encryption requirements, connection timeouts, application names, and read-routing intent (%s). The application name parameter deserves special attention — it shows up in %s, making it far easier to identify which service is responsible for a problematic query.""" % (code('ApplicationIntent=ReadOnly'), code('sys.dm_exec_sessions'))),

# 5 TLS
("""PostgreSQL supports several SSL modes — %s, %s, %s, %s, %s, and %s — and the choice affects both security and performance. In production, anything less than %s can expose you to man-in-the-middle risks, but many teams ship with %s and skip certificate validation. SQL Server uses encrypted connections controlled at both the server and driver level, and the %s flag in the connection string is a common shortcut that bypasses certificate validation in ways that should make any security-conscious DBA uncomfortable.""" % (code('disable'), code('allow'), code('prefer'), code('require'), code('verify-ca'), code('verify-full'), code('verify-full'), code('require'), code('TrustServerCertificate')),
 """SQL Server encrypts connections under control of both server and driver: the server's Force Encryption setting and the %s / %s connection-string keywords. The %s flag is a common shortcut that bypasses certificate validation in ways that should make any security-conscious DBA uncomfortable — in production, deploy proper certificates and require encryption rather than trusting whatever the server presents.""" % (code('Encrypt'), code('TrustServerCertificate'), code('TrustServerCertificate'))),

# 6 idle timeouts
("""Both databases close idle connections after a timeout (configurable via %s in PostgreSQL and connection timeout settings in SQL Server), and applications that lack reconnection logic will begin throwing errors in ways that look like database problems but are actually driver-level issues.""" % code('tcp_keepalives_idle'),
 """SQL Server closes idle connections after keepalive timeouts, and applications that lack reconnection logic will begin throwing errors in ways that look like database problems but are actually driver-level issues. Every data-access layer needs retry logic for transient failures — failovers, restarts, and network blips — not just a single open attempt."""),

# 7 connection model
("""PostgreSQL's process-per-connection model means that every new connection spawns an operating system process. At low concurrency this is fine. Under sustained load with hundreds or thousands of clients, the cost of process creation, memory overhead per connection, and context-switching becomes significant. SQL Server uses a thread-based model that handles concurrency somewhat better natively, but even there, uncontrolled connection counts create resource contention and can exhaust server-side connection limits.""",
 """SQL Server uses a thread-based connection model: each connection gets a worker thread from the thread pool. This handles concurrency better than process-per-connection designs, but uncontrolled connection counts still create resource contention — scheduler pressure, thread-stack memory, and worker-thread exhaustion under thousands of active connections. Pooling remains essential, and it starts in the driver, not the database."""),

# 8 PgBouncer -> ADO.NET pooling
("""<strong class="text-white">PgBouncer</strong> is the de facto connection pooler for PostgreSQL in production. It operates in three modes: session pooling (one server connection per client session, barely better than no pooling), transaction pooling (server connection returned to pool after each transaction, the most common production choice), and statement pooling (server connection returned after each statement, rarely used due to constraints it imposes). Transaction pooling is the right default for almost every OLTP workload.""",
 """<strong class="text-white">ADO.NET / SqlClient connection pooling</strong> is the standard pooling mechanism for .NET applications — and the pattern every SQL Server stack should mirror. The driver maintains a pool of long-lived connections keyed by the exact connection string; application Open() calls check out a pooled connection instead of establishing a new one. Pool size is governed by %s and %s in the connection string; %s and %s control recycling. Pooling is in-process — no extra tier to operate — but that means it is per application process: a fleet of 50 app servers each with a 100-connection pool is still 5,000 database connections, so size Max Pool Size against your fleet, not a single instance.""" % (code('Min Pool Size'), code('Max Pool Size'), code('Connection Lifetime'), code('Connection Reset'))),

# 9 pooler config intro
("""PgBouncer's configuration file controls pool sizes, authentication methods, and per-database limits:""",
 """A production SqlClient connection string puts the pooling knobs where every developer can see them:"""),

# 10 pgbouncer config block -> connection string example
("""<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>[databases]
myapp = host=127.0.0.1 port=5432 dbname=myapp

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
server_idle_timeout = 600
log_connections = 0
log_disconnections = 0</code></pre>""",
 POOLING_CONNSTR),

# 11 session-state caveat
("""One important architectural note: when using PgBouncer in transaction mode, features that depend on session-level state become unreliable. Prepared statements, advisory locks, %s configuration, and temporary tables all live at the session level. If your application relies on these across transaction boundaries, you either need session pooling, or you need to refactor the application to avoid session-level state. This is one of the more consequential tradeoffs in the PostgreSQL integration world.""" % code('SET LOCAL'),
 """One important architectural note: pooled connections are reset between uses via %s, which clears most session state — temp tables are dropped, SET options revert, open transactions roll back. If your application relies on session-level state surviving across Open/Close boundaries, it will break under pooling. That is the point: keep pooled work stateless and short, and never hold a pooled connection open across user think time.""" % code('sp_reset_connection')),

# 12 Pgpool-II -> middle tier
("""<strong class="text-white">Pgpool-II</strong> is an alternative that offers connection pooling alongside load balancing and query routing. It can automatically send read queries to replicas and writes to the primary, which makes it a meaningful architectural component rather than just a pooler. The tradeoff is operational complexity — Pgpool-II has more moving parts and is harder to operate correctly. For most teams, PgBouncer with an application-level read/write split is a simpler and more transparent approach.""",
 """For stacks outside .NET, or where centralized pooling is required, the same job is done one layer out: ODBC and JDBC drivers pool connections the same way SqlClient does, and a middle-tier pool (or the application's own shared pool) multiplexes many app servers onto fewer database connections. For read/write splitting, SQL Server's Always On listener with %s routing handles the split more cleanly than an external query router in most shops.""" % code('ApplicationIntent')),

# 13 remote data intro
("""There are legitimate scenarios where data that logically belongs together lives in separate databases — legacy systems that cannot be migrated, vendor-owned databases, archival stores, or analytical databases that need to be queried alongside operational data. Both PostgreSQL and SQL Server have mechanisms for querying remote data sources without moving the data first.""",
 """There are legitimate scenarios where data that logically belongs together lives in separate databases — legacy systems that cannot be migrated, vendor-owned databases, archival stores, or analytical databases that need to be queried alongside operational data. SQL Server has mechanisms for querying remote data sources without moving the data first."""),

# 14 FDW -> linked servers
("""PostgreSQL's <strong class="text-white">Foreign Data Wrapper (FDW)</strong> framework is a formal extension API that allows PostgreSQL to treat external data sources as if they were local tables. %s ships with PostgreSQL and allows cross-instance querying between PostgreSQL servers. %s, %s (for SQL Server), %s, %s, and dozens of community wrappers exist for other data sources.""" % (code('postgres_fdw'), code('mysql_fdw'), code('tds_fdw'), code('oracle_fdw'), code('file_fdw')),
 """SQL Server's <strong class="text-white">linked servers</strong> let T-SQL query remote data sources as if they were local — other SQL Server instances, Oracle, and any OLE DB/ODBC source. Distributed queries reference four-part names (%s) or %s for pass-through SQL executed on the remote side, which is usually the better choice for anything non-trivial.""" % (code('server.database.schema.table'), code('OPENQUERY'))),

# 15 fdw setup
("""Setting up %s involves three steps: creating the foreign server object, creating a user mapping, and then creating foreign tables that map to remote tables.""" % code('postgres_fdw'),
 """Setting up a linked server involves two steps: registering the remote with %s and configuring the login mapping with %s — then queries use four-part names. Keep the security mapping explicit: map specific local logins to specific remote credentials rather than a blanket self-mapping, and remember that linked-server queries execute in the security context of that mapping.""" % (code('sp_addlinkedserver'), code('sp_addlinkedsrvlogin'))),

# 16 pushdown
("""The query planner is aware of FDW tables and will push down WHERE clauses, JOINs, and aggregations to the remote server when the FDW implementation supports it (%s does). This pushdown behavior is significant — without it, PostgreSQL would fetch entire remote tables over the network and filter locally, which is catastrophically slow for large tables. You can verify what gets pushed down using %s, which will show %s clauses in the plan for FDW nodes.""" % (code('postgres_fdw'), code('EXPLAIN VERBOSE'), code('Remote SQL')),
 """The optimizer pushes WHERE clauses to the remote server when it can — collation-compatible predicates on indexed remote columns — but non-pushable filters pull entire remote tables over the network and filter locally, which is catastrophically slow. Verify with the actual execution plan: Remote Query operators show the SQL sent to the linked server, and anything missing from it is being filtered on your side. When in doubt, write the remote portion as %s with hand-tuned SQL.""" % code('OPENQUERY')),

# 17 bulk loading
("""<strong class="text-white">Bulk loading</strong> is the most efficient way to get large volumes of data into either database. PostgreSQL's %s command and SQL Server's %s / %s utility bypass row-by-row processing and write data in bulk, with significantly lower overhead per row than individual %s statements.""" % (code('COPY'), code('BULK INSERT'), code('bcp'), code('INSERT')),
 """<strong class="text-white">Bulk loading</strong> is the most efficient way to get large volumes of data into the database. SQL Server's %s statement and the %s utility bypass row-by-row processing and write data in bulk, with significantly lower overhead per row than individual %s statements. Use minimal-logging prerequisites (SIMPLE or BULK_LOGGED recovery, TABLOCK, empty target or appropriate trace flags) to keep large loads from exploding the transaction log.""" % (code('BULK INSERT'), code('bcp'), code('INSERT'))),

# 18 MERGE
("""The %s statement (in SQL Server, called %s; in PostgreSQL, called %s or the %s statement available since PostgreSQL 15) handles the common upsert pattern: insert new rows, update existing rows.""" % (code('MERGE'), code('MERGE'), code('INSERT ... ON CONFLICT'), code('MERGE')),
 """The %s statement handles the common upsert pattern: insert new rows, update existing rows, in a single atomic operation. Write it carefully — MERGE has well-documented edge cases around concurrency and Halloween protection; many shops prefer separate INSERT/UPDATE statements with proper locking hints for hot paths.""" % code('MERGE')),

# 19 CDC
("""SQL Server has built-in CDC support that can be enabled per table. PostgreSQL relies on logical replication — either via the built-in %s plugin or tools like <strong class="text-white">Debezium</strong>, which reads PostgreSQL's logical replication stream and publishes changes to Kafka. Debezium has become one of the most widely deployed integration tools in the PostgreSQL ecosystem, enabling streaming data pipelines from PostgreSQL into data warehouses, Elasticsearch, or other databases.""" % code('pgoutput'),
 """SQL Server has built-in CDC support enabled per table with %s: row changes land in change tables that ETL jobs can poll, or that Debezium's SQL Server connector streams into Kafka. Either path enables streaming pipelines from SQL Server into data warehouses, Elasticsearch, or downstream databases without triggers on the base tables.""" % code('sys.sp_cdc_enable_table')),

# 20 CDC DBA role
("""Enabling logical replication on PostgreSQL requires setting %s in %s and ensuring the tables you want to capture have primary keys (or replica identity set appropriately). The DBA's role in a CDC pipeline is to ensure that %s is configured correctly, that replication slots are monitored (an unconsumed replication slot will cause WAL accumulation that can fill your disk), and that the pipeline consumer is healthy enough to keep up with the change stream.""" % (code('wal_level = logical'), code('postgresql.conf'), code('wal_level')),
 """Tables captured by CDC need primary keys. The DBA's role in a CDC pipeline is to monitor capture-job latency, keep the cleanup job's retention aligned with consumer lag (an unconsumed change feed grows change tables until the disk fills), and confirm the pipeline consumer is healthy enough to keep up with the change stream."""),

# 21 cloud intro
("""As databases have moved into cloud and hybrid environments, DBAs must understand how their PostgreSQL or SQL Server instances connect to managed services, object storage, analytics platforms, and event systems.""",
 """As databases have moved into cloud and hybrid environments, DBAs must understand how their SQL Server instances connect to managed services, object storage, analytics platforms, and event systems."""),

# 22 cloud bulk
("""<strong class="text-white">Cloud-managed databases</strong> — Amazon RDS, Aurora, Azure SQL Database, Google Cloud SQL, Azure Database for PostgreSQL — expose the same SQL interfaces as on-premises instances, but some integration mechanisms change. Direct filesystem access for %s is unavailable on managed instances, replaced by cloud-native alternatives. On Amazon RDS for PostgreSQL, %s extension handles S3-based COPY operations. On Azure SQL Database, %s can reference Azure Blob Storage. These are not just convenience features — in a serverless or containerized pipeline architecture, there is no shared filesystem, and cloud-native bulk load paths become necessary.""" % (code('COPY FROM'), code('aws_s3'), code('BULK INSERT')),
 """<strong class="text-white">Cloud-managed databases</strong> — Azure SQL Database, SQL Server on Azure VMs, Amazon RDS for SQL Server — expose the same SQL interfaces as on-premises instances, but some integration mechanisms change. Direct filesystem access for %s is unavailable on managed instances, replaced by cloud-native alternatives. On Azure SQL Database, %s and %s can reference Azure Blob Storage directly. These are not just convenience features — in a serverless or containerized pipeline architecture, there is no shared filesystem, and cloud-native bulk load paths become necessary.""" % (code('BULK INSERT'), code('BULK INSERT'), code('OPENROWSET'))),
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
    print(f'ch16: all {len(REPLACEMENTS)} replacements applied')

main()
