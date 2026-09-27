#!/usr/bin/env python3
"""Apply ch31 phrase-level rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch31-edge.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
("PostgreSQL and SQL Server both have deployment stories in these environments, and as a DBA working in 2024 and beyond, understanding how to design, deploy, and maintain databases at the edge is no longer optional.",
 "SQL Server has a real deployment story in these environments through Azure SQL Edge, and understanding how to design, deploy, and maintain those databases is no longer optional."),
("how to architect PostgreSQL and SQL Server deployments for constrained and intermittently connected environments,",
 "how to architect SQL Server deployments for constrained and intermittently connected environments,"),
("aggressive parallel query execution, large shared_buffers, synchronous replication, frequent vacuum",
 "aggressive parallel query execution, large buffer pools, synchronous replication, frequent index maintenance"),

("""PostgreSQL is particularly common at the edge because it is open source, runs on ARM processors and Linux variants without licensing complications, and has a small memory footprint when properly tuned. SQL Server has a dedicated edge offering — Azure SQL Edge — that runs as a container on ARM64 and x64 hardware, specifically targeting IoT and industrial scenarios. Understanding both tools' capabilities in constrained environments gives you flexibility when the workload or the organization demands it.""",
 """SQL Server has a dedicated edge offering — Azure SQL Edge — that runs as a container on ARM64 and x64 hardware, specifically targeting IoT and industrial scenarios. It brings the familiar T-SQL engine, Query Store, and CDC to devices with as little as a few gigabytes of RAM, so the same skills, DMVs, and scripts you use in the datacenter transfer directly to the field."""),

("""Partitioning by time is almost always appropriate for edge telemetry workloads. On PostgreSQL, declarative range partitioning on a timestamp column allows you to drop old partitions instantly — no slow DELETE operations that generate WAL and lock rows. On SQL Server, partitioned tables using a partition function achieve similar results, though the management syntax is more verbose.""",
 """Partitioning by time is almost always appropriate for edge telemetry workloads. On SQL Server, partitioned tables using a partition function and sliding-window maintenance let you drop old partitions instantly with SWITCH — no slow DELETE operations that fill the log and lock rows. Partition elimination also keeps edge queries scanning only the recent partitions they actually need."""),

("""Compression is another lever. PostgreSQL's TOAST mechanism automatically compresses columns exceeding roughly 2 KB, but for structured numeric data in regular-sized columns, you get no automatic compression. TimescaleDB — a PostgreSQL extension widely used in edge IoT scenarios — provides columnar compression for hypertables that can reduce storage by 90% for typical telemetry data. On SQL Server, row and page compression are available even in the Edge edition and are straightforward to enable:""",
 """Compression is another lever. On SQL Server, row and page compression are available even in the Edge edition and are straightforward to enable — page compression routinely halves the footprint of numeric telemetry data. For the most aggressive storage savings, clustered columnstore indexes (supported on Azure SQL Edge) compress telemetry several-fold and accelerate analytic scans:"""),

("""Write-ahead log (WAL) sizing on PostgreSQL edge nodes deserves attention. The default %s is needed for logical replication used in sync strategies, but the WAL segments will accumulate if sync is interrupted. Setting %s to a value appropriate for your storage budget — not the server default — prevents WAL from consuming the disk during a multi-day connectivity outage.""" % (code('wal_level = replica'), code('max_wal_size')),
 """Transaction log sizing on SQL Server edge nodes deserves attention. The log cannot truncate past the oldest active transaction, so it will accumulate if sync or backups are interrupted. Size the log for your storage budget and monitor %s — during a multi-day connectivity outage, an unshipped log on a constrained disk is fatal.""" % code('log_reuse_wait_desc')),

("""In this pattern, the edge node buffers rows locally and periodically flushes them upstream. PostgreSQL logical replication handles this natively. Configure the edge as a publication and the central server as a subscriber. When the connection is interrupted, the replication slot on the edge retains WAL until the subscriber reconnects. When connectivity resumes, the central server catches up automatically.""",
 """In this pattern, the edge node buffers rows locally and periodically flushes them upstream. Transactional replication handles this natively: the edge node is the publisher, the central server is the subscriber, and the distribution database buffers changes while disconnected. When connectivity resumes, the distribution agent catches the subscriber up automatically."""),

("""The risk here is slot bloat. A replication slot that cannot drain will cause WAL to accumulate indefinitely on the edge node. On a constrained disk, this is fatal. Set %s conservatively and monitor %s for %s lag. If lag exceeds your storage budget, you must either expand storage, reduce the outage tolerance, or switch to a polling-based sync approach that does not use slots.""" % (code('wal_keep_size'), code('pg_replication_slots'), code('restart_lsn')),
 """The risk here is distribution backlog. Undistributed commands accumulate in the distribution database indefinitely while the edge node is disconnected. On a constrained disk, this is fatal. Set the distribution retention conservatively and monitor the backlog of undistributed commands. If the backlog exceeds your storage budget, you must either expand storage, reduce the outage tolerance, or switch to a polling-based sync approach."""),

("<strong class=\"text-white\">Checkpoint-based polling</strong> is an alternative to replication slots that is more robust during extended outages.",
 "<strong class=\"text-white\">Checkpoint-based polling</strong> is an alternative to log-based replication that is more robust during extended outages."),

("""There is no direct equivalent in PostgreSQL, which is why the trigger-based %s approach is standard there.""" % code('modified_at'),
 """For tables without a rowversion column, a trigger-maintained %s timestamp is the fallback.""" % code('modified_at')),

("""For PostgreSQL on a 4 GB edge node, a conservative baseline configuration looks like this: %s (not the commonly cited 25%% of RAM — the OS page cache also serves PostgreSQL and you need headroom), %s (with a hard ceiling to prevent parallel sort operations from collectively exhausting RAM), %s (edge applications typically have small connection pools), %s, and %s. Parallel query is valuable on large servers; on edge hardware, it competes with other processes for CPU time and does not deliver proportional benefit.""" % (code('shared_buffers = 512MB'), code('work_mem = 4MB'), code('max_connections = 20'), code('max_parallel_workers = 2'), code('max_parallel_workers_per_gather = 1')),
 """For SQL Server on a 4 GB edge node, a conservative baseline configuration looks like this: %s (leave headroom for the OS and the container runtime), %s, %s, and small application connection pools (edge applications rarely need more than a dozen connections). Parallel query is valuable on large servers; on edge hardware, it competes with other processes for CPU time and does not deliver proportional benefit.""" % (code('max server memory = 2048MB'), code('max degree of parallelism = 2'), code('cost threshold for parallelism = 50'))),

("""WAL configuration for edge reliability: set %s. This sounds counterintuitive — the common advice is to set it to %s for write performance — but on edge hardware where power can be interrupted without warning, losing committed transactions is unacceptable. The durability guarantee is worth the modest write latency increase. Set %s to spread checkpoint I/O across a longer window, reducing disk throughput spikes.""" % (code('synchronous_commit = on'), code('off'), code('checkpoint_completion_target = 0.9')),
 """Log durability for edge reliability: keep the transaction log on the most reliable storage attached to the device and never trade durability knobs for write performance — on edge hardware where power can be interrupted without warning, losing committed transactions is unacceptable. Set the recovery interval modestly so crash recovery completes quickly when the device restarts."""),

("""Autovacuum behavior in PostgreSQL needs explicit attention on edge deployments. The default autovacuum is calibrated for large servers. On edge hardware, autovacuum running at the wrong time can spike I/O and CPU, causing ingestion latency spikes visible in the telemetry data you are trying to collect. Configure %s and %s to throttle autovacuum's I/O consumption. For insert-heavy tables with no updates or deletes (common in sensor ingestion), autovacuum's role is primarily freezing transaction IDs — the default settings cause it to run more aggressively than needed. Set %s on these tables to reduce unnecessary vacuum runs.""" % (code('autovacuum_vacuum_cost_delay = 20ms'), code('autovacuum_vacuum_cost_limit = 200'), code('autovacuum_vacuum_scale_factor = 0.2')),
 """Index and statistics maintenance on edge deployments needs explicit attention. Automatic maintenance is calibrated for servers with idle windows; on edge hardware, a rebuild firing at the wrong time spikes I/O and CPU, causing ingestion latency spikes visible in the telemetry data you are trying to collect. Schedule maintenance in known-idle windows and keep it lightweight — reorganize instead of rebuild where possible. For insert-only sensor tables, fragmentation is minimal; the main job is keeping statistics current so the optimizer doesn't choose nested loops over millions of rows."""),

("Placing PostgreSQL's WAL on a separate storage device from the data files eliminates the I/O contention that causes most edge write latency issues.",
 "Placing SQL Server's transaction log on a separate storage device from the data files eliminates the I/O contention that causes most edge write latency issues."),
("For SQL Server, the same separation of data files and log files applies.",
 "The same separation of data files and log files applies on any engine."),

("""Key metrics to collect locally every minute include: active connection count, longest running query duration, replication slot lag (in bytes), table bloat estimates from %s, cache hit ratio from %s, and available disk space. On SQL Server Edge, equivalent metrics come from %s, %s, and %s.""" % (code('pg_stat_user_tables'), code('pg_stat_database'), code('sys.dm_os_performance_counters'), code('sys.dm_exec_requests'), code('sys.dm_os_sys_info')),
 """Key metrics to collect locally every minute include: active connection count, longest running query duration, replication backlog, index fragmentation from %s, page life expectancy from %s, and available disk space. Long-running sessions come from %s, and instance-level counters from %s.""" % (code('sys.dm_db_index_physical_stats'), code('sys.dm_os_performance_counters'), code('sys.dm_exec_requests'), code('sys.dm_os_sys_info'))),

("""use certificate-based authentication for PostgreSQL (%s, %s) or SQL Server's certificate-based login, provisioned at deployment time.""" % (code('ssl_cert_file'), code('ssl_key_file')),
 """use certificate-based authentication — SQL Server's certificate-based logins, provisioned at deployment time."""),

("You cannot roll out a PostgreSQL major version upgrade to hundreds of field devices the way you upgrade a cloud instance.",
 "You cannot roll out a SQL Server CU upgrade to hundreds of field devices the way you upgrade a cloud instance."),

("""PostgreSQL's %s can run on edge hardware for major version upgrades, but it requires the old and new binaries to coexist temporarily, which may be a storage concern on constrained devices. Dump-and-restore through %s / %s is slower but has a simpler failure mode. For SQL Server Edge, in-place upgrades of the container image are the standard mechanism.""" % (code('pg_upgrade'), code('pg_dump'), code('pg_restore')),
 """For SQL Server Edge, in-place upgrades of the container image are the standard mechanism: pull the new image, recreate the container against the same persistent volume, and let crash recovery bring the databases online. For major version jumps, back up first — downgrading a container image does not downgrade the database files."""),

("On Linux with PostgreSQL, full disk encryption via LUKS (Linux Unified Key Setup) is the standard approach.",
 "On Linux edge devices, full disk encryption via LUKS (Linux Unified Key Setup) is the standard approach. Enable TDE on the SQL Server databases as well, so the data files stay encrypted even if the volume is detached from the device."),

("""PostgreSQL's %s should be configured to reject all connections except from localhost and the VPN interface. Reject password authentication in favor of %s or certificate authentication. SQL Server should have all unnecessary protocols disabled — only TCP/IP over the VPN interface should be active, and the SQL Server Browser service should be disabled.""" % (code('pg_hba.conf'), code('scram-sha-256')),
 """The SQL Server instance should accept connections only from localhost and the VPN interface — disable all unnecessary protocols so only TCP/IP over the VPN interface is active, and disable the SQL Server Browser service. Prefer Windows or certificate authentication over SQL logins with passwords."""),

("""PostgreSQL's %s with %s and %s is a practical starting point. SQL Server Audit configured to capture server-level events and DDL changes gives equivalent coverage.""" % (code("log_statement = 'ddl'"), code('log_connections = on'), code('log_disconnections = on')),
 """SQL Server Audit configured to capture server-level events and DDL changes is the practical starting point; keep the audit target small and roll it aggressively so it never competes with telemetry for disk."""),

("""Use UUID primary keys generated locally (PostgreSQL's %s, SQL Server's %s for index-friendly UUIDs) or allocate sequence ranges""" % (code('gen_random_uuid()'), code('NEWSEQUENTIALID()')),
 """Use UUID primary keys generated locally (%s for index-friendly UUIDs) or allocate sequence ranges""" % code('NEWSEQUENTIALID()')),

("""PostgreSQL's WAL guarantees crash recovery, but only if %s is enabled (it is, by default — do not disable it on edge hardware to chase write performance). SQL Server's write-ahead logging provides the same guarantee. After each simulated power loss, verify row counts, check for corruption with %s or %s, and validate that the sync checkpoint is consistent.""" % (code('fsync'), code('pg_dump'), code('DBCC CHECKDB')),
 """SQL Server's write-ahead logging guarantees crash recovery — never disable write-through behavior on edge hardware to chase write performance. After each simulated power loss, verify row counts, check for corruption with %s, and validate that the sync checkpoint is consistent.""" % code('DBCC CHECKDB')),

("Run pgbench (PostgreSQL) or the equivalent against your edge hardware at ingest rates",
 "Run an ingest load generator (HammerDB or a custom T-SQL loop) against your edge hardware at ingest rates"),
("shared_buffers eviction causing blks_read to spike, autovacuum triggering during the peak and competing for I/O, WAL write latency growing until commit latency becomes user-visible.",
 "buffer pool eviction causing physical reads to spike, automatic maintenance triggering during the peak and competing for I/O, log write latency growing until commit latency becomes user-visible."),

("(TimescaleDB for PostgreSQL, page compression for SQL Server) are the primary tools",
 "(columnstore and page compression for SQL Server) are the primary tools"),
("checkpoint-based polling with `ROWVERSION` (SQL Server) or trigger-maintained `modified_at` timestamps (PostgreSQL) is more robust",
 "checkpoint-based polling with `ROWVERSION` or trigger-maintained `modified_at` timestamps is more robust"),
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
    print(f'ch31: all {len(REPLACEMENTS)} replacements applied')

main()
