#!/usr/bin/env python3
"""Rewrite ch05 sections 5.3-5.5 (part B)."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch05-architecture-patterns.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

NL = "\n"
BS = "\\"
CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'
reps = []

# 5.3 storage
reps.append((
"Maximum gp3 performance is 16,000 IOPS and 1,000 MB/s. For PostgreSQL workloads with heavy random I/O — OLTP with small row updates, index-heavy queries — gp3 at 12,000–16,000 IOPS covers the majority of production workloads on instances up to db.r6g.8xlarge.",
"Maximum gp3 performance is 16,000 IOPS and 1,000 MB/s. For SQL Server workloads with heavy random I/O — OLTP with small row updates, index-heavy queries — gp3 at 12,000–16,000 IOPS covers the majority of production workloads on instances up to db.r6i.8xlarge."
))
reps.append((
"At these levels you're typically also running db.r6g.16xlarge or db.r6i.32xlarge, where the network bandwidth to the EBS volume (25–50 Gbps) becomes the binding constraint",
"At these levels you're typically also running db.r6i.16xlarge or db.r6i.32xlarge, where the network bandwidth to the EBS volume (25–50 Gbps) becomes the binding constraint"
))
reps.append((
"However, Aurora storage doesn't shrink automatically — once expanded to 50TB, the billing floor is 50TB even if you delete data. Run <code " + CODE + ">VACUUM</code> and monitor <code " + CODE + ">aurora_storage_utilization</code> to understand actual versus allocated space.",
"However, Aurora storage doesn't shrink automatically — once expanded to 50TB, the billing floor is 50TB even if you delete data. Rebuild fragmented indexes to reclaim space where possible and monitor <code " + CODE + ">aurora_storage_utilization</code> to understand actual versus allocated space."
))

# Aurora storage queries -> Aurora MySQL
PG_STORAGE_Q = (
"<code>-- Query Aurora storage utilization (run from psql connected to Aurora)" + NL +
"SELECT " + NL +
"    current_setting('server_version') AS pg_version," + NL +
"    pg_size_pretty(sum(pg_database_size(datname))) AS total_logical_size," + NL +
"    -- Aurora-specific storage stats via aurora_stat_utils extension" + NL +
"    pg_size_pretty(" + NL +
"        (SELECT sum(allocated_storage) " + NL +
"         FROM aurora_storage_object_stats() " + NL +
"         WHERE object_type = 'data')" + NL +
"    ) AS aurora_allocated_storage;" + NL + NL +
"-- Monitor bloat that inflates Aurora storage costs" + NL +
"SELECT " + NL +
"    schemaname," + NL +
"    tablename," + NL +
"    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size," + NL +
"    pg_size_pretty(" + NL +
"        pg_total_relation_size(schemaname||'.'||tablename) - " + NL +
"        pg_relation_size(schemaname||'.'||tablename)" + NL +
"    ) AS bloat_estimate," + NL +
"    n_dead_tup," + NL +
"    last_autovacuum" + NL +
"FROM pg_stat_user_tables" + NL +
"WHERE n_dead_tup &gt; 100000" + NL +
"ORDER BY n_dead_tup DESC" + NL +
"LIMIT 20;</code>"
)
MYSQL_STORAGE_Q = (
"<code>-- Aurora MySQL: compare logical table sizes against billed storage" + NL +
"-- Billed storage itself is visible in CloudWatch under the VolumeBytesUsed metric" + NL +
"SELECT " + NL +
"    table_schema," + NL +
"    ROUND(SUM(data_length + index_length) / 1024 / 1024 / 1024, 2) AS size_gb," + NL +
"    COUNT(*) AS tables" + NL +
"FROM information_schema.tables" + NL +
"WHERE table_schema NOT IN ('mysql', 'performance_schema', 'information_schema', 'sys')" + NL +
"GROUP BY table_schema" + NL +
"ORDER BY size_gb DESC;" + NL + NL +
"-- Find the largest tables driving storage growth" + NL +
"SELECT " + NL +
"    table_schema," + NL +
"    table_name," + NL +
"    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb" + NL +
"FROM information_schema.tables" + NL +
"WHERE table_schema NOT IN ('mysql', 'performance_schema', 'information_schema', 'sys')" + NL +
"ORDER BY size_mb DESC" + NL +
"LIMIT 20;</code>"
)
reps.append((PG_STORAGE_Q, MYSQL_STORAGE_Q))

# 5.4 network
reps.append((
"#### The pg_hba.conf Replacement",
"#### The Server-Login Replacement"
))
reps.append((
"On premises, <code " + CODE + ">pg_hba.conf</code> controlled which hosts could connect to PostgreSQL and with what authentication method. In the cloud, that control is split across multiple layers, and understanding which layer does what determines whether you have a security gap.",
"On premises, Windows Firewall rules and SQL Server logins controlled which hosts could connect and with what authentication method. In the cloud, that control is split across multiple layers, and understanding which layer does what determines whether you have a security gap."
))
reps.append((
"For a production RDS instance, you should never open port 5432 to <code " + CODE + ">0.0.0.0/0</code>.",
"For a production RDS instance, you should never open port 1433 to <code " + CODE + ">0.0.0.0/0</code>."
))
reps.append((
"3. RDS security group allows inbound 5432 only from <code " + CODE + ">sg-app-tier</code>",
"3. RDS security group allows inbound 1433 only from <code " + CODE + ">sg-app-tier</code>"
))
reps.append((
"# Allow PostgreSQL port from app security group only" + NL +
"aws ec2 authorize-security-group-ingress " + BS + NL +
"  --group-id ${RDS_SG_ID} " + BS + NL +
"  --protocol tcp " + BS + NL +
"  --port 5432 " + BS,
"# Allow SQL Server port from app security group only" + NL +
"aws ec2 authorize-security-group-ingress " + BS + NL +
"  --group-id ${RDS_SG_ID} " + BS + NL +
"  --protocol tcp " + BS + NL +
"  --port 1433 " + BS
))
# Cloud SQL PSC -> SQL Server
reps.append((
"gcloud sql instances create prod-cloudsql-pg " + BS + NL +
"  --database-version=POSTGRES_15 " + BS,
"gcloud sql instances create prod-cloudsql-sqlserver " + BS + NL +
"  --database-version=SQLSERVER_2022_STANDARD " + BS
))
# (describe is covered inside the PG_FLAGS block below)
reps.append((
"gcloud compute forwarding-rules create prod-cloudsql-psc-endpoint " + BS,
"gcloud compute forwarding-rules create prod-cloudsql-psc-endpoint " + BS
))

# 5.5 parameter tuning
reps.append((
"On premises, you had full authority over <code " + CODE + ">postgresql.conf</code> — every GUC was yours to set. In managed cloud environments, you work within parameter groups (AWS), server parameters (Azure), and database flags (GCP), and some parameters that matter most to performance are fixed or bounded by the managed service.",
"On premises, you had full authority over <code " + CODE + ">sp_configure</code> and the SQL Server surface area. In managed cloud environments, you work within parameter groups (AWS), server properties (Azure), and database flags (GCP), and some settings that matter most to performance are fixed or bounded by the managed service."
))
reps.append((
"The parameters you <strong class=\"text-white\">cannot change</strong> in RDS PostgreSQL:</p>" + NL +
"<li class=\"flex gap-2 text-gray-300\"><span class=\"text-blue-400\">→</span> `max_connections` — configurable but bounded by instance class (db.r6g.large forces a lower ceiling than on-premises because RDS manages memory for its own processes)</li>" + NL +
"<li class=\"flex gap-2 text-gray-300\"><span class=\"text-blue-400\">→</span> `wal_level` — always `logical` in RDS (which is actually more permissive than on-premises defaults)</li>" + NL +
"<li class=\"flex gap-2 text-gray-300\"><span class=\"text-blue-400\">→</span> `archive_mode` — always `on` in RDS (RDS manages WAL archival for backups and Point-in-Time Recovery)</li>" + NL +
"<li class=\"flex gap-2 text-gray-300\"><span class=\"text-blue-400\">→</span> `superuser` access — you get `rds_superuser` role, not true PostgreSQL superuser; certain system catalog writes and extensions requiring superuser are unavailable</li>",
"The settings you <strong class=\"text-white\">cannot change</strong> in RDS for SQL Server:</p>" + NL +
"<li class=\"flex gap-2 text-gray-300\"><span class=\"text-blue-400\">→</span> `max server memory (MB)` — managed by AWS based on instance class; you cannot set it directly in the parameter group</li>" + NL +
"<li class=\"flex gap-2 text-gray-300\"><span class=\"text-blue-400\">→</span> SQL Server Agent — not available on RDS for SQL Server at all; scheduled jobs move to Lambda/EventBridge or an external scheduler</li>" + NL +
"<li class=\"flex gap-2 text-gray-300\"><span class=\"text-blue-400\">→</span> `clr enabled` — restricted to the approved assembly set; arbitrary CLR code is unavailable</li>" + NL +
"<li class=\"flex gap-2 text-gray-300\"><span class=\"text-blue-400\">→</span> `sysadmin` access — you get a master user, not true sysadmin; certain server-level operations and trace flags are unavailable</li>"
))
reps.append((
"The parameters you <strong class=\"text-white\">should</strong> tune in RDS PostgreSQL parameter groups:",
"The parameters you <strong class=\"text-white\">should</strong> tune in RDS for SQL Server parameter groups:"
))

# pg_settings query -> sys.configurations
PG_SETTINGS_Q = (
"<code>-- Check current settings and their sources (run from psql)" + NL +
"SELECT " + NL +
"    name," + NL +
"    setting," + NL +
"    unit," + NL +
"    source," + NL +
"    context," + NL +
"    short_desc" + NL +
"FROM pg_settings" + NL +
"WHERE name IN (" + NL +
"    'shared_buffers'," + NL +
"    'effective_cache_size'," + NL +
"    'work_mem'," + NL +
"    'maintenance_work_mem'," + NL +
"    'max_worker_processes'," + NL +
"    'max_parallel_workers'," + NL +
"    'max_parallel_workers_per_gather'," + NL +
"    'checkpoint_completion_target'," + NL +
"    'wal_buffers'," + NL +
"    'default_statistics_target'," + NL +
"    'random_page_cost'," + NL +
"    'effective_io_concurrency'," + NL +
"    'autovacuum_vacuum_scale_factor'," + NL +
"    'autovacuum_analyze_scale_factor'," + NL +
"    'autovacuum_vacuum_cost_delay'," + NL +
"    'log_min_duration_statement'," + NL +
"    'log_autovacuum_min_duration'" + NL +
")" + NL +
"ORDER BY name;</code>"
)
SQL_CONFIG_Q = (
"<code>-- Check current settings and their sources on RDS for SQL Server" + NL +
"SELECT " + NL +
"    name," + NL +
"    value," + NL +
"    value_in_use," + NL +
"    description," + NL +
"    is_dynamic," + NL +
"    is_advanced" + NL +
"FROM sys.configurations" + NL +
"WHERE name IN (" + NL +
"    'max server memory (MB)'," + NL +
"    'max degree of parallelism'," + NL +
"    'cost threshold for parallelism'," + NL +
"    'fill factor (%)'," + NL +
"    'optimize for ad hoc workloads'," + NL +
"    'backup compression default'," + NL +
"    'remote query timeout (s)'," + NL +
"    'blocked process threshold (s)'" + NL +
")" + NL +
"ORDER BY name;</code>"
)
reps.append((PG_SETTINGS_Q, SQL_CONFIG_Q))
reps.append((
"In AWS, you apply these through a parameter group. For RDS, changes to parameters with <code " + CODE + ">context = postmaster</code> require an instance reboot; <code " + CODE + ">context = sighup</code> parameters apply without a reboot.",
"In AWS, you apply these through a parameter group. For RDS, parameters marked <code " + CODE + ">ApplyMethod=pending-reboot</code> require an instance reboot; <code " + CODE + ">ApplyMethod=immediate</code> parameters apply without a reboot."
))

# RDS param group CLI -> SQL Server
reps.append((
"# Create a custom RDS parameter group for PostgreSQL 15" + NL +
"aws rds create-db-parameter-group " + BS + NL +
"  --db-parameter-group-name prod-postgres15-params " + BS + NL +
"  --db-parameter-group-family postgres15 " + BS + NL +
'  --description "Production PostgreSQL 15 parameters"',
"# Create a custom RDS parameter group for SQL Server 2022" + NL +
"aws rds create-db-parameter-group " + BS + NL +
"  --db-parameter-group-name prod-sql2022-params " + BS + NL +
"  --db-parameter-group-family sqlserver-se-16.0 " + BS + NL +
'  --description "Production SQL Server 2022 parameters"'
))
reps.append((
"# Apply key performance parameters" + NL +
"aws rds modify-db-parameter-group " + BS + NL +
"  --db-parameter-group-name prod-postgres15-params " + BS + NL +
"  --parameters " + BS + NL +
'    "ParameterName=effective_cache_size,ParameterValue=75%,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=work_mem,ParameterValue=65536,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=maintenance_work_mem,ParameterValue=2097152,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=checkpoint_completion_target,ParameterValue=0.9,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=default_statistics_target,ParameterValue=200,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=random_page_cost,ParameterValue=1.1,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=effective_io_concurrency,ParameterValue=200,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=autovacuum_vacuum_scale_factor,ParameterValue=0.02,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=autovacuum_analyze_scale_factor,ParameterValue=0.01,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=autovacuum_vacuum_cost_delay,ParameterValue=2,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=log_autovacuum_min_duration,ParameterValue=0,ApplyMethod=immediate"',
"# Apply key performance parameters" + NL +
"aws rds modify-db-parameter-group " + BS + NL +
"  --db-parameter-group-name prod-sql2022-params " + BS + NL +
"  --parameters " + BS + NL +
'    "ParameterName=max server memory (MB),ParameterValue={DBInstanceClassMemory/1048576}*3/4,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=max degree of parallelism,ParameterValue=8,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=cost threshold for parallelism,ParameterValue=50,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=fill factor (%),ParameterValue=90,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=optimize for ad hoc workloads,ParameterValue=1,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=backup compression default,ParameterValue=1,ApplyMethod=immediate"'
))
reps.append((
"> <strong class=\"text-white\">Note on <code " + CODE + ">shared_buffers</code> in RDS</strong>: AWS manages <code " + CODE + ">shared_buffers</code> automatically based on instance class and sets it to 25% of total instance RAM, which is the standard PostgreSQL recommendation. You can override this in the parameter group, but AWS will not let you set it above a ceiling they manage — and exceeding 40% of available RAM in a managed environment where RDS also has memory reserved for its own processes can trigger OOM conditions. Accept the managed default here unless you have profiled evidence of a specific benefit.",
"> <strong class=\"text-white\">Note on <code " + CODE + ">max server memory (MB)</code> in RDS</strong>: AWS manages <code " + CODE + ">max server memory</code> automatically based on instance class, leaving headroom for the OS and RDS management processes. You can influence it through the parameter group formula syntax, but AWS will not let you set it above a ceiling they manage — and over-allocating memory in a managed environment where RDS reserves memory for its own processes can trigger OOM conditions. Accept the managed default here unless you have profiled evidence of a specific benefit."
))

# GCP Cloud SQL Flags -> SQL Server
reps.append((
"Cloud SQL exposes PostgreSQL configuration through database flags in the instance settings. The syntax and behavior mirror standard PostgreSQL GUCs; the constraint is that flags requiring a postmaster restart trigger a brief instance restart automatically when applied via gcloud or the Console.",
"Cloud SQL exposes SQL Server configuration through database flags in the instance settings. The documented flag set for Cloud SQL for SQL Server is much narrower than the PostgreSQL flag list — most tuning moves to database-scoped configuration, Query Store settings, and query design instead. Flags that require a restart trigger a brief instance restart automatically when applied via gcloud or the Console."
))
PG_FLAGS = (
"<code># Apply PostgreSQL performance flags to Cloud SQL instance" + NL +
"gcloud sql instances patch prod-cloudsql-pg " + BS + NL +
"  --database-flags " + BS + NL +
"    work_mem=65536," + BS + NL +
"    maintenance_work_mem=2097152," + BS + NL +
"    effective_cache_size=25165824," + BS + NL +
"    checkpoint_completion_target=0.9," + BS + NL +
"    default_statistics_target=200," + BS + NL +
"    random_page_cost=1.1," + BS + NL +
"    effective_io_concurrency=200," + BS + NL +
"    autovacuum_vacuum_scale_factor=0.02," + BS + NL +
"    autovacuum_analyze_scale_factor=0.01," + BS + NL +
"    autovacuum_vacuum_cost_delay=2," + BS + NL +
"    log_min_duration_statement=1000," + BS + NL +
"    log_autovacuum_min_duration=0" + NL + NL +
"# Verify applied flags" + NL +
"gcloud sql instances describe prod-cloudsql-pg " + BS + NL +
'  --format="yaml(settings.databaseFlags)"</code>'
)
SQL_FLAGS = (
"<code># Apply SQL Server database flags to a Cloud SQL for SQL Server instance" + NL +
"# (check the current GCP documentation for the supported flag list — it is intentionally narrow)" + NL +
"gcloud sql instances patch prod-cloudsql-sqlserver " + BS + NL +
"  --database-flags " + BS + NL +
"    contained\\ database\\ authentication=on" + NL + NL +
"# Verify applied flags" + NL +
"gcloud sql instances describe prod-cloudsql-sqlserver " + BS + NL +
'  --format="yaml(settings.databaseFlags)"</code>'
)
reps.append((PG_FLAGS, SQL_FLAGS))
reps.append((
"A Cloud SQL-specific constraint worth noting: <code " + CODE + ">max_connections</code> in Cloud SQL is tied to instance memory, and Cloud SQL sets a default that is lower than you might configure on a self-managed instance of the same RAM size. This is because Cloud SQL reserves memory for its HA and proxy infrastructure. If your application opens large connection pools against Cloud SQL without an intermediate connection pooler (PgBouncer on a GCE VM, or the Cloud SQL Auth Proxy with connection limiting), you'll hit <code " + CODE + ">max_connections</code> errors under load. Plan for this upfront and size connection pools against the actual <code " + CODE + ">max_connections</code> value, not the RAM-derived estimate from your on-premises experience.",
"A Cloud SQL-specific constraint worth noting: the <code " + CODE + ">user connections</code> ceiling in Cloud SQL for SQL Server is tied to instance memory, and Cloud SQL sets a default that is lower than you might configure on a self-managed instance of the same RAM size. This is because Cloud SQL reserves memory for its HA and proxy infrastructure. If your application opens large connection pools against Cloud SQL without an intermediate connection pooler (HikariCP on a GCE VM, or the Cloud SQL Auth Proxy with connection limiting), you'll hit connection errors under load. Plan for this upfront and size connection pools against the actual <code " + CODE + ">user connections</code> value, not the RAM-derived estimate from your on-premises experience."
))

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
print("ch05-B OK:", len(reps), "replacements")
