#!/usr/bin/env python3
"""Rewrite ch06 sections 6.1-6.2 (part A)."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch06-rds-deep-dive.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

NL = "\n"
BS = "\\"
CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'
reps = []

# 6.1 intro
reps.append((
"RDS supports six database engines: MySQL, PostgreSQL, MariaDB, Oracle, Microsoft SQL Server, and Amazon Aurora (which gets its own chapter, but shares the RDS console). Each engine runs on a managed EC2 instance underneath, and the distinction between \"RDS for PostgreSQL\" and \"self-managed PostgreSQL on EC2\" is not just operational convenience — it represents a fundamental trade-off in control.",
"RDS supports six database engines: Microsoft SQL Server, MySQL, PostgreSQL, MariaDB, Oracle, and Amazon Aurora (which gets its own chapter, but shares the RDS console). Each engine runs on a managed EC2 instance underneath, and the distinction between \"RDS for SQL Server\" and \"self-managed SQL Server on EC2\" is not just operational convenience — it represents a fundamental trade-off in control."
))
reps.append((
"What you lose versus self-managed PostgreSQL on EC2:",
"What you lose versus self-managed SQL Server on EC2:"
))
reps.append((
"→ No `pg_hba.conf` direct editing. Authentication rules are enforced through security groups, IAM database authentication, and SSL certificate requirements set via parameter groups.",
"→ No direct server-property editing. Authentication rules are enforced through security groups, IAM database authentication, and TLS requirements set via parameter groups."
))
reps.append((
"→ No superuser. The `rds_superuser` role grants most capabilities, but it is not true superuser — you cannot load arbitrary shared libraries, and you cannot access system catalogs in ways that require true OS-level privilege.",
"→ No sysadmin. The master user grants most capabilities, but it is not true sysadmin — you cannot enable arbitrary trace flags, use the dedicated admin connection freely, or load unapproved CLR assemblies."
))
reps.append((
"→ No WAL archive access. You can enable WAL archiving to S3 for logical replication, but you cannot read the raw WAL files directly.",
"→ No transaction log file access. You cannot read the raw LDF files directly; transaction log backups are managed by RDS."
))
reps.append((
"→ No `pg_basebackup` from the instance. Backups are managed by RDS using EBS snapshots.",
"→ No `BACKUP DATABASE` to local disk. Backups are managed by RDS; native backups to S3 require the SQLSERVER_BACKUP_RESTORE option group."
))
reps.append((
"→ Multi-AZ failover handled by the platform without you managing Pacemaker or Patroni.",
"→ Multi-AZ failover handled by the platform without you managing Windows Server Failover Clustering."
))
reps.append((
"PostgreSQL 11 reached end of life on AWS in 2023 and instances still running it received forced upgrades. You should never run more than one major version behind current in production.",
"SQL Server 2012 reached end of extended support and AWS deprecated it on RDS — instances still running deprecated versions receive forced upgrade notices. You should never run more than one major version behind current in production."
))
reps.append((
"# List all available PostgreSQL engine versions in us-east-1" + NL +
"aws rds describe-db-engine-versions " + BS + NL +
"  --engine postgres " + BS,
"# List all available SQL Server engine versions in us-east-1" + NL +
"aws rds describe-db-engine-versions " + BS + NL +
"  --engine sqlserver-se " + BS
))
reps.append((
"aws rds describe-db-engine-versions " + BS + NL +
"  --engine postgres " + BS + NL +
"  --query 'DBEngineVersions[?contains(SupportedFeatureNames, `kerberos`) == `true`].[EngineVersion]'",
"aws rds describe-db-engine-versions " + BS + NL +
"  --engine sqlserver-se " + BS + NL +
"  --query 'DBEngineVersions[?contains(SupportedFeatureNames, `kerberos`) == `true`].[EngineVersion]'"
))
reps.append((
"(pg_catalog views changed significantly between PostgreSQL 13 and 14, for example).",
"(system behavior changed between SQL Server 2019 and 2022, for example)."
))
# global renames for prod-postgres-01 (2 occurrences in 6.1)
t = t.replace(
    "--db-instance-identifier prod-postgres-01 " + BS,
    "--db-instance-identifier prod-sql-01 " + BS
)

# 6.2
reps.append((
"Graviton instances offer 10–20% better price-performance for PostgreSQL and MySQL workloads compared to equivalent Intel or AMD instances. The catch: SQL Server and Oracle are not supported on Graviton because AWS cannot run those binaries on ARM. PostgreSQL and MySQL have native ARM builds that run well on Graviton.",
"Graviton instances offer 10–20% better price-performance for PostgreSQL and MySQL workloads compared to equivalent Intel or AMD instances — but that is irrelevant for SQL Server: SQL Server and Oracle are not supported on Graviton because AWS cannot run those binaries on ARM. For RDS for SQL Server, always choose the Intel families (db.r7i, db.m7i); there is no ARM option."
))
t = t.replace(
    "Name=DBInstanceIdentifier,Value=dev-postgres-t4g",
    "Name=DBInstanceIdentifier,Value=dev-sql-t3"
)
reps.append((
"Sizing recommendations for PostgreSQL migration: When migrating a self-managed PostgreSQL instance, the most important metric from your source system is shared_buffers utilization — specifically, what fraction of your working set fits in the buffer cache. On RDS, shared_buffers defaults to 25% of instance memory for PostgreSQL. A db.r7g.4xlarge has 128 GB of RAM, giving you ~32 GB of shared_buffers. If your on-premises system has a 40 GB buffer pool with reasonable hit rates, move to db.r7g.8xlarge (256 GB RAM, ~64 GB shared_buffers) with headroom.",
"Sizing recommendations for SQL Server migration: When migrating a self-managed SQL Server instance, the most important metrics from your source system describe buffer pool behavior — Page Life Expectancy (PLE), buffer cache hit ratio, and lazy writes/sec. On RDS for SQL Server, max server memory is managed by AWS based on instance class. A db.r7i.4xlarge has 128 GB of RAM. If your on-premises system has a 40 GB buffer pool with a healthy PLE and a buffer cache hit ratio above 95%, move to db.r7i.8xlarge (256 GB RAM) with headroom."
))

PG_SIZING_Q = (
"<code>-- Run this on your SOURCE PostgreSQL instance before migration" + NL +
"-- to understand buffer cache behavior" + NL + NL +
"-- Buffer hit rate (should be &gt;95% in production)" + NL +
"SELECT " + NL +
"    sum(heap_blks_hit) AS heap_hits," + NL +
"    sum(heap_blks_read) AS heap_reads," + NL +
"    round(" + NL +
"        sum(heap_blks_hit)::numeric / " + NL +
"        nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100, 2" + NL +
"    ) AS buffer_hit_rate_pct" + NL +
"FROM pg_statio_user_tables;" + NL + NL +
"-- Working set estimate: tables + indexes that fit in cache" + NL +
"SELECT " + NL +
"    schemaname," + NL +
"    relname AS table_name," + NL +
"    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) AS total_size," + NL +
"    round(" + NL +
"        heap_blks_hit::numeric / nullif(heap_blks_hit + heap_blks_read, 0) * 100, 1" + NL +
"    ) AS table_hit_rate_pct" + NL +
"FROM pg_statio_user_tables" + NL +
"WHERE heap_blks_hit + heap_blks_read &gt; 10000" + NL +
"ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC" + NL +
"LIMIT 20;" + NL + NL +
"-- Identify tables causing physical reads (candidates for shared_buffers increase)" + NL +
"SELECT " + NL +
"    schemaname," + NL +
"    relname," + NL +
"    heap_blks_read AS physical_reads," + NL +
"    heap_blks_hit AS cache_hits" + NL +
"FROM pg_statio_user_tables" + NL +
"WHERE heap_blks_read &gt; 1000" + NL +
"ORDER BY heap_blks_read DESC" + NL +
"LIMIT 10;</code>"
)
SQL_SIZING_Q = (
"<code>-- Run this on your SOURCE SQL Server instance before migration" + NL +
"-- to understand buffer pool behavior" + NL + NL +
"-- Buffer Manager counters (PLE healthy range scales with RAM: roughly 300s per 4GB)" + NL +
"SELECT counter_name, cntr_value" + NL +
"FROM sys.dm_os_performance_counters" + NL +
"WHERE object_name LIKE '%Buffer Manager%'" + NL +
"  AND counter_name IN (" + NL +
"    'Buffer cache hit ratio'," + NL +
"    'Page life expectancy'," + NL +
"    'Lazy writes/sec'," + NL +
"    'Checkpoint pages/sec'" + NL +
"  );" + NL + NL +
"-- Working set estimate: buffer pool usage by database" + NL +
"SELECT DB_NAME(database_id) AS database_name," + NL +
"       COUNT(*) * 8 / 1024 AS buffer_pool_mb" + NL +
"FROM sys.dm_os_buffer_descriptors" + NL +
"GROUP BY database_id" + NL +
"ORDER BY buffer_pool_mb DESC;" + NL + NL +
"-- Memory pressure signals: stolen pages and out-of-memory notifications" + NL +
"SELECT counter_name, cntr_value" + NL +
"FROM sys.dm_os_performance_counters" + NL +
"WHERE object_name LIKE '%Memory Manager%'" + NL +
"  AND counter_name IN ('Stolen Server Memory (KB)', 'Out of memory errors');</code>"
)
reps.append((PG_SIZING_Q, SQL_SIZING_Q))

failed = []
for old, new in reps:
    n = t.count(old)
    if n == 1:
        t = t.replace(old, new)
    else:
        failed.append((n, old[:90]))

if failed:
    print("FAILED:")
    for n, s in failed:
        print("  count=" + str(n) + ": " + s)
    sys.exit(1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch06-A OK:", len(reps), "replacements")
