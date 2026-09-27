#!/usr/bin/env python3
"""Apply ch30 phrase-level rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch30-cloud.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

# Entry 9 needs literal % signs, built without %-formatting:
old9 = ("<strong class=\"text-white\">Memory and shared_buffers in the cloud.</strong> PostgreSQL's "
        + code('shared_buffers')
        + " is typically set to 25PCT of instance RAM on managed services by default. On a "
        + code('db.r7g.2xlarge')
        + " with 64 GB RAM, that's 16 GB. For read-heavy OLAP workloads, you can push this to 40PCT "
        + "— but on managed RDS you do this through parameter groups, not "
        + code('postgresql.conf') + " directly.")
old9 = old9.replace('PCT', '%')
new9 = ("<strong class=\"text-white\">Memory and max server memory in the cloud.</strong> On a "
        + code('db.r6g.2xlarge')
        + " with 64 GB RAM, set max server memory to roughly 56 GB — but on managed RDS you do this through parameter groups, not a config file directly. Azure SQL Database abstracts this further: vCore tiers bundle the memory sizing, and serverless tiers auto-scale it with the workload.")

REPLACEMENTS = [
("Running PostgreSQL or SQL Server in the cloud is no longer a specialized skill",
 "Running SQL Server in the cloud is no longer a specialized skill"),
("(AWS RDS, Amazon Aurora, Azure SQL Database, Azure Database for PostgreSQL, Google Cloud SQL)",
 "(AWS RDS for SQL Server, Azure SQL Database, Azure SQL Managed Instance, Google Cloud SQL for SQL Server)"),
("or install extensions that the provider has not whitelisted.",
 "or install components the provider has not enabled."),
("You install PostgreSQL or SQL Server yourself, configure storage, manage patches,",
 "You install SQL Server yourself, configure storage, manage patches,"),
("(PostGIS, pg_partman at a version the provider hasn't adopted, or advanced SQL Server features like PolyBase)",
 "(a specific CU, advanced features like PolyBase, or OS-level trace flags)"),

("""<strong class="text-white">AWS RDS for PostgreSQL</strong> and <strong class="text-white">Amazon Aurora PostgreSQL</strong> are distinct offerings. RDS is a managed community PostgreSQL with a subset of extensions available. Aurora PostgreSQL is a cloud-native reimplementation of the PostgreSQL wire protocol on top of a distributed storage layer. Aurora's shared storage model means replicas share the same underlying storage rather than streaming WAL — which makes failover faster (typically under 30 seconds) but changes how you think about replication lag and storage costs.""",
 """<strong class="text-white">AWS RDS for SQL Server</strong> and <strong class="text-white">Azure SQL Managed Instance</strong> are the two most common managed SQL Server homes. RDS runs SQL Server on EC2 under the hood with automated patching, backups, and Multi-AZ failover. Managed Instance offers near-100% compatibility with on-premises SQL Server — including SQL Server Agent, CDC, and cross-database queries — inside your own VNet, which makes it the natural lift-and-shift target."""),

("""<strong class="text-white">Azure Database for PostgreSQL</strong> comes in two modes: Flexible Server (the current, recommended offering) and the legacy Single Server (which Microsoft is retiring). Flexible Server gives you a real choice of availability zones, stop/start capability for dev environments, and more parameter customization than earlier Azure Postgres offerings.""",
 """<strong class="text-white">Azure SQL Database</strong> comes in three flavors: single databases (serverless or provisioned — the simplest start), elastic pools (many databases sharing a resource pool — the microservices answer), and Managed Instance (the lift-and-shift answer). The Hyperscale tier adds storage that grows toward 100 TB with fast scaling and readable replicas."""),

("""<strong class="text-white">Google Cloud SQL</strong> supports both PostgreSQL and SQL Server. It is a solid managed offering but lags behind RDS and Azure in extension availability and advanced configuration surface area.""",
 """<strong class="text-white">Google Cloud SQL for SQL Server</strong> is a solid managed offering for straightforward workloads, but lags behind RDS and Azure in advanced configuration surface area and SQL Server feature depth."""),

("""For PostgreSQL on RDS or Aurora, instance classes map to EC2 instance families: %s instances are burstable (appropriate for dev/test, dangerous in production under sustained load), %s and %s are general-purpose and memory-optimized respectively. For SQL Server-heavy workloads on RDS, the %s family (memory-optimized) is almost always the right choice because SQL Server's buffer pool benefits disproportionately from RAM.""" % (code('db.t4g'), code('db.m7g'), code('db.r7g'), code('db.r')),
 """On RDS, instance classes map to EC2 families: %s burstable (dev/test only — dangerous in production under sustained load), %s general-purpose, %s memory-optimized. For SQL Server on RDS, the %s family is almost always the right choice because the buffer pool benefits disproportionately from RAM.""" % (code('db.t4g'), code('db.m7g'), code('db.r7g'), code('db.r'))),

(old9, new9),

("On Azure, Azure Database for PostgreSQL Flexible Server supports VNet integration, which puts the managed service inside your own VNet rather than on a shared network with a service endpoint. This is the preferred model.",
 "On Azure, Managed Instance lives inside your VNet natively; Azure SQL Database uses private endpoints to bring the managed service into your VNet. Either way, no public endpoint for production."),
("on the database port (5432 for PostgreSQL, 1433 for SQL Server) only from",
 "on the database port (1433) only from"),
("""On RDS PostgreSQL, enforce this by setting %s in the parameter group. On Azure Database for PostgreSQL Flexible Server, SSL is enforced by default and can be configured for TLS version minimums.""" % code('rds.force_ssl = 1'),
 """On RDS for SQL Server, enforce encryption with %s in the parameter group and %s on clients. On Azure SQL Database, TLS is enforced by default with configurable minimum versions.""" % (code('rds.force_ssl'), code('Encrypt=yes'))),
("AWS RDS supports IAM database authentication for PostgreSQL and MySQL",
 "AWS RDS supports IAM database authentication for SQL Server"),
("Azure SQL Database supports Azure Active Directory authentication in the same vein.",
 "Azure SQL Database supports Microsoft Entra (Azure AD) authentication in the same vein."),

("""<strong class="text-white">Aurora's Multi-AZ</strong> is architecturally different. The shared storage layer is inherently replicated across three AZs — there's no traditional "standby with WAL replay." Failover promotes one of the read replicas to become the new writer, which is faster (typically 20–30 seconds) and does not require storage synchronization. Aurora also supports up to 15 read replicas sharing the same storage cluster.""",
 """<strong class="text-white">RDS Multi-AZ</strong> keeps a synchronous standby in another availability zone and fails over automatically, typically in 60–120 seconds. Multi-AZ DB clusters add readable standbys for read scaling. Either way the standby is fully managed — you don't provision, patch, or monitor it as a separate server."""),

("""<strong class="text-white">Azure Database for PostgreSQL Flexible Server</strong> with zone-redundant HA maintains a hot standby in a different availability zone with synchronous replication. Failover is automatic and typically completes in under 60 seconds. The standby is not readable — a design decision consistent with RDS Multi-AZ.""",
 """<strong class="text-white">Azure SQL Database</strong> zone-redundant HA keeps replicas across availability zones with automatic failover, typically under 60 seconds. Business Critical and Hyperscale tiers add readable secondaries; even single databases without zone redundancy get local redundancy inside the datacenter."""),

("""A %s RDS PostgreSQL instance has a default max_connections around 200.""" % code('db.r7g.large'),
 """A %s RDS SQL Server instance caps out at a few hundred connections.""" % code('db.r6g.large')),
("PgBouncer (for PostgreSQL) or a connection proxy layer is essential.",
 "A connection proxy layer is essential."),

("Automated backups on RDS</strong> consist of daily snapshots plus continuous WAL archiving.",
 "Automated backups on RDS</strong> consist of daily snapshots plus transaction log backups every 5 minutes."),
("replays WAL to your target time.",
 "replays log to your target time."),

("""<strong class="text-white">Azure Database for PostgreSQL Flexible Server</strong> automated backups follow a similar model: full backups weekly, differential backups daily, WAL backups every 5 minutes. PITR is available to the nearest 5-minute boundary within your retention period (7–35 days).""",
 """<strong class="text-white">Azure SQL Database</strong> automated backups follow a similar model: full backups weekly, differentials every 12–24 hours, log backups every 5–10 minutes. PITR is available within your retention period (7–35 days depending on tier)."""),

("PostgreSQL tables that are frequently updated accumulate dead tuples. On managed services, autovacuum handles reclamation, but it does not return freed space to the OS",
 "Tables that are frequently updated accumulate fragmentation and forwarded records. Rebuilds and reorganizes reclaim space within the database, but they do not return freed space to the OS"),
("""To reclaim actual storage on RDS PostgreSQL, you need %s (which takes an access exclusive lock) or %s (which many managed services now support via extensions). Monitor storage growth trends and investigate tables with high bloat ratios before they grow into a storage tier increase.""" % (code('VACUUM FULL'), code('pg_repack')),
 """To reclaim actual storage on a managed service, rebuild the table into a new filegroup or move it to a fresh database during a window — there is no online shrink-to-fit. Size storage for the high-water mark, not the current size, and monitor growth trends before they grow into a storage tier increase."""),

("Memory pressure calls for a memory-optimized instance or reducing %s." % code('max_connections'),
 "Memory pressure calls for a memory-optimized instance or capping connection counts."),
("when investigating a cloud PostgreSQL or SQL Server slowdown.",
 "when investigating a cloud SQL Server slowdown."),

("""On RDS PostgreSQL, %s should be set to %s to spread checkpoint I/O across a longer window, reducing write spikes.""" % (code('checkpoint_completion_target'), code('0.9')),
 """On RDS for SQL Server, the parameters that matter are the familiar ones: max server memory sized to the instance, MAXDOP matched to vCPUs, and cost threshold for parallelism raised from the default 5. Set them in the parameter group once and re-verify after every instance resize — a resize that doubles vCPUs without touching MAXDOP leaves parallelism misconfigured."""),
("""%s should be reduced to %s for databases backed by SSD storage (which all cloud databases are) — the default of %s was designed for spinning disk and will cause the planner to prefer sequential scans over index scans inappropriately on cloud storage. %s should be set to %s""" % (code('random_page_cost'), code('1.1'), code('4.0'), code('effective_io_concurrency'), code('200')),
 """There is no cloud-specific planner knob to chase on SQL Server — the equivalent of those tunings is keeping statistics current and the buffer pool warm, which matters more on cloud storage where the first cold read pays full provisioned-IOPS latency"""),

("<strong class=\"text-white\">PostgreSQL parameter group recommendations for cloud deployments:</strong>",
 "<strong class=\"text-white\">SQL Server parameter group recommendations for cloud deployments:</strong>"),

("""-- Verify cloud-appropriate planner and I/O settings
SELECT name,
       setting,
       unit,
       boot_val,
       source
FROM   pg_settings
WHERE  name IN (
    'random_page_cost',
    'effective_io_concurrency',
    'checkpoint_completion_target',
    'checkpoint_timeout',
    'default_statistics_target',
    'max_parallel_workers_per_gather',
    'max_parallel_workers',
    'log_min_duration_statement',
    'log_autovacuum_min_duration'
)
ORDER BY name;""",
 """-- Verify cloud-appropriate engine settings
SELECT name,
       value_in_use,
       description
FROM   sys.configurations
WHERE  name IN (
    'max server memory (MB)',
    'min server memory (MB)',
    'max degree of parallelism',
    'cost threshold for parallelism',
    'backup compression default',
    'optimize for ad hoc workloads'
)
ORDER BY name;"""),

("""<strong class="text-white">Autovacuum tuning in cloud PostgreSQL</strong> often requires adjustment from the managed service defaults. The default autovacuum cost delay and scale factors are conservative — they prevent autovacuum from impacting foreground workloads at the expense of allowing table bloat to accumulate. On high-write workloads, consider tuning at the table level for your most actively written tables:""",
 """<strong class="text-white">Index maintenance tuning in cloud SQL Server</strong> often requires adjustment from the managed service defaults. Fragmentation accumulates the same way in the cloud, but your maintenance windows may be tighter and IOPS may be provisioned — and billed. Prioritize by fragmentation level and page count: rebuilding a 10-page index wastes IOPS, while reorganizing a 30%-fragmented large index during business hours burns provisioned throughput. Maintain only what the metrics say needs it:"""),

("""-- Tune autovacuum aggressiveness for a high-write table
ALTER TABLE orders
    SET (autovacuum_vacuum_scale_factor = 0.01,
         autovacuum_vacuum_cost_delay   = 2,
         autovacuum_analyze_scale_factor = 0.005);

-- Monitor autovacuum activity across tables
SELECT schemaname,
       relname,
       n_live_tup,
       n_dead_tup,
       ROUND(100.0 * n_dead_tup
             / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
       last_vacuum,
       last_autovacuum,
       last_analyze,
       last_autoanalyze,
       vacuum_count,
       autovacuum_count
FROM   pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT  20;""",
 """-- Find indexes worth maintaining, ordered by fragmentation
SELECT
    OBJECT_SCHEMA_NAME(ips.object_id) + '.' + OBJECT_NAME(ips.object_id) AS table_name,
    i.name AS index_name,
    ips.avg_fragmentation_in_percent,
    ips.page_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i
    ON ips.object_id = i.object_id
    AND ips.index_id = i.index_id
WHERE ips.page_count > 1000
  AND ips.avg_fragmentation_in_percent > 30
ORDER BY ips.avg_fragmentation_in_percent DESC;"""),

("What PostgreSQL or SQL Server version does the managed target service support? Which extensions are in use, and are they available on the managed platform?",
 "What SQL Server version and edition does the managed target service support? Which features are in use (Agent jobs, CDC, linked servers, CLR), and are they available on the managed platform?"),
("(pg_dump for PostgreSQL, native backup for SQL Server), transfer, and restore.",
 "(native backup to URL for SQL Server), transfer, and restore."),
("Use logical replication (PostgreSQL) or transactional replication/log shipping (SQL Server) to keep the target in sync",
 "Use transactional replication, log shipping, or distributed availability groups to keep the target in sync"),
("AWS Database Migration Service (DMS) and Azure Database Migration Service support both modes for PostgreSQL and SQL Server.",
 "AWS Database Migration Service (DMS) and Azure Database Migration Service support both modes for SQL Server."),
("""AWS DMS using PostgreSQL logical replication requires the %s to be set to %s on the source, and the replication slot must be monitored carefully — an inactive replication slot accumulates WAL indefinitely and can fill your source disk if the migration stalls.""" % (code('wal_level'), code('logical')),
 """AWS DMS using CDC on a SQL Server source requires CDC enabled on the source database, and the replication instance must keep up — a stalled migration accumulates changes in the source log and distribution database, so monitor capture latency, not just row counts."""),

("| Metric | PostgreSQL | SQL Server | Alert threshold |",
 "| Metric | CloudWatch / Azure Monitor source | Alert threshold |"),
("| Connection count | DatabaseConnections | DatabaseConnections | >80% of max_connections |",
 "| Connection count | DatabaseConnections | >80% of the instance connection limit |"),
("""For PostgreSQL specifically, connection count alerting is particularly important because %s on managed services is often lower than teams expect, and connection exhaustion causes complete application outages with minimal warning.""" % code('max_connections'),
 """Connection count alerting is particularly important on managed services because connection caps are lower than teams expect, and connection exhaustion causes complete application outages with minimal warning."""),
("""RDS publishes PostgreSQL logs to CloudWatch Logs, where you can create metric filters for patterns like %s, %s, %s, %s, and %s. The last pattern is especially important — autovacuum running in wraparound prevention mode is an emergency signal that your transaction ID consumption is approaching the danger zone.""" % (code('ERROR'), code('FATAL'), code('lock timeout'), code('deadlock detected'), code('autovacuum.*to prevent wraparound')),
 """RDS publishes SQL Server error logs to CloudWatch Logs, where you can create metric filters for patterns like %s, %s, and %s. The last pattern is the storage-stall canary — sustained long I/O stalls mean the storage layer, not the query, is the problem.""" % (code('Error'), code('deadlock'), code('I/O requests taking longer than 15 seconds'))),
("(available for RDS PostgreSQL and SQL Server) provides a timeline",
 "(available for RDS for SQL Server) provides a timeline"),
("RDS, Azure Database for PostgreSQL Flexible Server, and Aurora handle operational overhead",
 "RDS for SQL Server, Azure SQL Database, and Managed Instance handle operational overhead"),
("apply cloud-appropriate parameter settings (SSD-tuned `random_page_cost`, aggressive autovacuum on high-write tables, reserved instance pricing for stable production workloads)",
 "apply cloud-appropriate settings (max server memory and MAXDOP sized per instance, index maintenance tuned for provisioned IOPS, reserved instance pricing for stable production workloads)"),
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
    print(f'ch30: all {len(REPLACEMENTS)} replacements applied')

main()
