#!/usr/bin/env python3
"""Rewrite ch06 sections 6.5-6.8 + takeaways (part C)."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch06-rds-deep-dive.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

NL = "\n"
BS = "\\"
CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'
C = "<code " + CODE + ">"
STR = '<strong class="text-white">'
reps = []

# ---- 6.2 leftover ----
reps.append((
"SQL Server exposes fewer runtime-adjustable parameters through the RDS parameter group interface than PostgreSQL does.",
"SQL Server exposes fewer runtime-adjustable parameters through the RDS parameter group interface than a self-managed instance exposes through " + C + "sp_configure</code>."
))

# ---- 6.5 ----
reps.append((
C + "prod-postgres-primary.abc123.us-east-1.rds.amazonaws.com</code>",
C + "prod-sql-primary.abc123.us-east-1.rds.amazonaws.com</code>"
))
# Multi-AZ Cluster paragraph -> SQL Server reality
OLD_CLUSTER_PARA = (
STR + "Multi-AZ with two readable standbys (RDS Multi-AZ Cluster):</strong> AWS introduced a newer Multi-AZ option called Multi-AZ Cluster that provides two readable standby instances instead of one non-readable standby. This gives you read scalability built into the HA tier. It's available for MySQL 8.0 and PostgreSQL 13+. The cluster endpoint handles writes; reader endpoints handle reads. This is distinct from Aurora's multi-AZ model (covered in Chapter 7), and is worth considering for PostgreSQL workloads that need both HA and read scaling without the Aurora pricing model."
)
NEW_CLUSTER_PARA = (
STR + "Multi-AZ DB Cluster is not available for SQL Server:</strong> AWS offers a newer Multi-AZ option called Multi-AZ DB Cluster with two readable standby instances — but only for MySQL and PostgreSQL. It is <em>not</em> available for RDS for SQL Server. For SQL Server, Multi-AZ uses SQL Server Always On availability groups: the primary replica accepts writes, and the secondary replica exists solely for automatic failover. The secondary is not readable and cannot be queried directly."
)
reps.append((OLD_CLUSTER_PARA, NEW_CLUSTER_PARA))
reps.append((
STR + "RDS Multi-AZ Cluster configuration:</strong>",
STR + "Creating a Multi-AZ SQL Server instance:</strong>"
))
OLD_CLUSTER_CLI = (
"<code># Create a Multi-AZ Cluster for PostgreSQL (not a standard Multi-AZ instance)" + NL +
"aws rds create-db-cluster " + BS + NL +
"  --db-cluster-identifier prod-postgres-cluster " + BS + NL +
"  --engine postgres " + BS + NL +
"  --engine-version 16.3 " + BS + NL +
"  --db-cluster-instance-class db.r7g.4xlarge " + BS + NL +
'  --master-username dbadmin ' + BS + NL +
'  --master-user-password "${DB_PASSWORD}" ' + BS + NL +
"  --storage-type io1 " + BS + NL +
"  --iops 12000 " + BS + NL +
"  --allocated-storage 500 " + BS + NL +
"  --backup-retention-period 14 " + BS + NL +
"  --vpc-security-group-ids sg-0abc123def456789 " + BS + NL +
"  --db-subnet-group-name private-db-subnets " + BS + NL +
"  --region us-east-1</code>"
)
NEW_CLUSTER_CLI = (
"<code># Create a Multi-AZ SQL Server instance (Always On availability group under the hood)" + NL +
"aws rds create-db-instance " + BS + NL +
"  --db-instance-identifier prod-sql-primary " + BS + NL +
"  --db-instance-class db.r7i.4xlarge " + BS + NL +
"  --engine sqlserver-se " + BS + NL +
"  --engine-version 16.00 " + BS + NL +
'  --master-username dbadmin ' + BS + NL +
'  --master-user-password "${DB_PASSWORD}" ' + BS + NL +
"  --allocated-storage 500 " + BS + NL +
"  --storage-type gp3 " + BS + NL +
"  --multi-az " + BS + NL +
"  --backup-retention-period 14 " + BS + NL +
"  --vpc-security-group-ids sg-0abc123def456789 " + BS + NL +
"  --db-subnet-group-name private-db-subnets " + BS + NL +
"  --db-parameter-group-name sqlserver2022-prod " + BS + NL +
"  --region us-east-1</code>"
)
reps.append((OLD_CLUSTER_CLI, NEW_CLUSTER_CLI))
# Read Replicas -> read scaling on RDS for SQL Server
reps.append((
STR + "Read Replicas: Asynchronous copies for read scaling and cross-region DR</strong>",
STR + "Read scaling on RDS for SQL Server: there are no read replicas</strong>"
))
reps.append((
"Read Replicas use asynchronous replication. The primary does not wait for the replica to confirm a write. This means:",
"Unlike MySQL and PostgreSQL, RDS for SQL Server does <em>not</em> offer read replicas — " + C + "create-db-instance-read-replica</code> is not supported for the " + C + "sqlserver-*</code> engines. This is the single biggest architectural difference to internalize: on RDS for SQL Server, read scaling must be designed explicitly. Your options are:"
))
OLD_RR_LIS = (
'<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> Replicas have some replication lag (usually sub-second to a few seconds on healthy systems, potentially minutes under heavy write load).</li>' + NL +
'<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> Replicas can serve reads, offloading analytical queries from the primary.</li>' + NL +
'<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> Replicas can be in different AWS regions (cross-region read replicas), which provides geographic DR.</li>' + NL +
'<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> A Read Replica can be promoted to a standalone primary — the promotion takes 5–15 minutes and creates a new independent instance.</li>'
)
NEW_RR_LIS = (
'<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> <strong class="text-white">Self-managed readable secondaries on EC2:</strong> run SQL Server on EC2 with an Always On availability group and add readable secondary replicas for reporting and analytics offload (covered in Chapter 8).</li>' + NL +
'<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> <strong class="text-white">Snapshot-refreshed reporting copies:</strong> restore a production snapshot to a separate RDS instance on a schedule (nightly or hourly) for reporting workloads that tolerate stale data.</li>' + NL +
'<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> <strong class="text-white">Cross-region DR via snapshot copy:</strong> copy automated or manual snapshots to a second region and restore them there — this is your geographic DR story, not replica promotion.</li>' + NL +
'<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> <strong class="text-white">Reduce primary read load first:</strong> before building read-scale infrastructure, verify the primary is not doing avoidable work — missing indexes, unparameterized ad hoc queries, and reporting queries that belong on a copy.</li>'
)
reps.append((OLD_RR_LIS, NEW_RR_LIS))
reps.append((
"Read Replicas are not a substitute for Multi-AZ on the primary. If your primary is Single-AZ and you have five Read Replicas, you still have a single point of failure on the primary. The correct production architecture is Multi-AZ primary with Read Replicas for read scaling.",
"Multi-AZ is not a read-scaling feature on RDS for SQL Server. The secondary replica cannot serve reads, so a Multi-AZ primary does nothing for read pressure. The correct production architecture is a Multi-AZ primary for failover <em>plus</em> an explicit read-scaling strategy (readable AG secondaries on EC2, or snapshot-refreshed reporting copies) sized to your reporting workload."
))
reps.append((
STR + "Creating Read Replicas:</strong>",
STR + "Cross-region snapshot copy for DR (the RDS-for-SQL-Server alternative to replica promotion):</strong>"
))
OLD_RR_CLI = (
"<code># Create a read replica in the same region" + NL +
"aws rds create-db-instance-read-replica " + BS + NL +
"  --db-instance-identifier prod-postgres-replica-01 " + BS + NL +
"  --source-db-instance-identifier prod-postgres-primary " + BS + NL +
"  --db-instance-class db.r7g.2xlarge " + BS + NL +
"  --availability-zone us-east-1b " + BS + NL +
"  --storage-type gp3 " + BS + NL +
"  --publicly-accessible false " + BS + NL +
"  --region us-east-1" + NL + NL +
"# Create a cross-region read replica (for DR or regional read scaling)" + NL +
"# Run this in the target region" + NL +
"aws rds create-db-instance-read-replica " + BS + NL +
"  --db-instance-identifier prod-postgres-replica-usw2 " + BS + NL +
"  --source-db-instance-identifier arn:aws:rds:us-east-1:123456789012:db:prod-postgres-primary " + BS + NL +
"  --db-instance-class db.r7g.2xlarge " + BS + NL +
"  --storage-type gp3 " + BS + NL +
"  --region us-west-2</code>"
)
NEW_RR_CLI = (
"<code># RDS for SQL Server has no create-db-instance-read-replica." + NL +
"# For cross-region DR, copy the latest automated snapshot and restore it." + NL +
"# Run the copy in the TARGET region:" + NL +
"aws rds copy-db-snapshot " + BS + NL +
"  --source-db-snapshot-identifier arn:aws:rds:us-east-1:123456789012:snapshot:rds:prod-sql-primary-2024-01-15-03-00 " + BS + NL +
"  --target-db-snapshot-identifier prod-sql-dr-copy-20240115 " + BS + NL +
"  --kms-key-id arn:aws:kms:us-west-2:123456789012:key/mrk-abc123 " + BS + NL +
"  --region us-west-2" + NL + NL +
"# Restore it as a DR/test instance in the target region" + NL +
"aws rds restore-db-instance-from-db-snapshot " + BS + NL +
"  --db-instance-identifier prod-sql-dr-usw2 " + BS + NL +
"  --db-snapshot-identifier prod-sql-dr-copy-20240115 " + BS + NL +
"  --db-instance-class db.r7i.2xlarge " + BS + NL +
"  --no-multi-az " + BS + NL +
"  --region us-west-2</code>"
)
reps.append((OLD_RR_CLI, NEW_RR_CLI))
reps.append((
STR + "Monitoring replication lag:</strong>",
STR + "Monitoring Multi-AZ health (the secondary is not directly queryable):</strong>"
))
OLD_LAG_CLI = (
"<code># CloudWatch metric for replication lag (in seconds)" + NL +
"aws cloudwatch get-metric-statistics " + BS + NL +
"  --namespace AWS/RDS " + BS + NL +
"  --metric-name ReplicaLag " + BS + NL +
"  --dimensions Name=DBInstanceIdentifier,Value=prod-postgres-replica-01 " + BS + NL +
"  --start-time 2024-01-15T00:00:00Z " + BS + NL +
"  --end-time 2024-01-15T23:59:59Z " + BS + NL +
"  --period 300 " + BS + NL +
"  --statistics Average Maximum " + BS + NL +
"  --output table</code>"
)
NEW_LAG_CLI = (
"<code># There is no ReplicaLag metric for RDS for SQL Server Multi-AZ." + NL +
"# Monitor failover and AG health through RDS events instead." + NL +
"# Subscribe to failover-related events:" + NL +
"aws rds create-event-subscription " + BS + NL +
"  --subscription-name prod-sql-failover-events " + BS + NL +
"  --sns-topic-arn arn:aws:sns:us-east-1:123456789012:db-alerts " + BS + NL +
"  --source-type db-instance " + BS + NL +
"  --source-ids prod-sql-primary " + BS + NL +
'  --event-categories "failover" "failure" ' + BS + NL +
"  --region us-east-1" + NL + NL +
"# Review recent failover/failure events" + NL +
"aws rds describe-events " + BS + NL +
"  --source-identifier prod-sql-primary " + BS + NL +
"  --source-type db-instance " + BS + NL +
"  --start-time 2024-01-14T00:00:00Z " + BS + NL +
"  --query 'Events[*].[Date,Message]' " + BS + NL +
"  --output table " + BS + NL +
"  --region us-east-1</code>"
)
reps.append((OLD_LAG_CLI, NEW_LAG_CLI))
OLD_PG_LAG_Q = (
"<code>-- PostgreSQL: Check replication lag from within the primary" + NL +
"SELECT" + NL +
"    client_addr," + NL +
"    state," + NL +
"    sent_lsn," + NL +
"    write_lsn," + NL +
"    flush_lsn," + NL +
"    replay_lsn," + NL +
"    pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) AS replay_lag_bytes," + NL +
"    write_lag," + NL +
"    flush_lag," + NL +
"    replay_lag" + NL +
"FROM pg_stat_replication" + NL +
"ORDER BY replay_lag DESC NULLS LAST;" + NL + NL +
"-- From within the replica: check how far behind primary" + NL +
"SELECT" + NL +
"    now() - pg_last_xact_replay_timestamp() AS replication_lag," + NL +
"    pg_is_in_recovery() AS is_replica," + NL +
"    pg_last_wal_receive_lsn() AS received_lsn," + NL +
"    pg_last_wal_replay_lsn() AS replayed_lsn," + NL +
"    pg_wal_lsn_diff(" + NL +
"        pg_last_wal_receive_lsn()," + NL +
"        pg_last_wal_replay_lsn()" + NL +
"    ) AS lag_bytes;</code>"
)
NEW_AG_Q = (
"<code>-- On RDS Multi-AZ for SQL Server the secondary replica is NOT queryable." + NL +
"-- For reference, this is the AG health query you would run on a" + NL +
"-- self-managed / EC2 Always On availability group:" + NL +
"SELECT ar.replica_server_name," + NL +
"       rs.role_desc," + NL +
"       rs.connected_state_desc," + NL +
"       rs.synchronization_state_desc," + NL +
"       DB_NAME(drs.database_id) AS database_name," + NL +
"       drs.synchronization_state_desc AS db_sync_state," + NL +
"       drs.log_send_queue_size AS log_send_queue_kb," + NL +
"       drs.redo_queue_size AS redo_queue_kb" + NL +
"FROM sys.dm_hadr_availability_replica_states rs" + NL +
"JOIN sys.availability_replicas ar" + NL +
"  ON rs.replica_id = ar.replica_id" + NL +
"JOIN sys.dm_hadr_database_replica_states drs" + NL +
"  ON drs.replica_id = rs.replica_id;" + NL + NL +
"-- On RDS, confirm Multi-AZ status from the control plane instead:" + NL +
"-- aws rds describe-db-instances --db-instance-identifier prod-sql-primary" + NL +
"--   --query 'DBInstances[0].[MultiAZ, SecondaryAvailabilityZone]'</code>"
)
reps.append((OLD_PG_LAG_Q, NEW_AG_Q))
# RDS Proxy
reps.append((
"# Create an RDS Proxy for the PostgreSQL instance",
"# Create an RDS Proxy for the SQL Server instance"
))
reps.append((
"  --db-proxy-name prod-postgres-proxy " + BS + NL + '  --engine-family POSTGRESQL ' + BS,
"  --db-proxy-name prod-sql-proxy " + BS + NL + '  --engine-family SQLSERVER ' + BS
))
reps.append((
'"SecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/postgres/dbadmin"',
'"SecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/sqlserver/dbadmin"'
))
reps.append((
"  --db-proxy-name prod-postgres-proxy " + BS + NL + "  --db-instance-identifiers prod-postgres-primary " + BS,
"  --db-proxy-name prod-sql-proxy " + BS + NL + "  --db-instance-identifiers prod-sql-primary " + BS
))
OLD_PROXY_LIM = (
"RDS Proxy has one significant limitation for PostgreSQL: it does not support all PostgreSQL authentication methods and it does not support all connection parameters. Specifically, it does not support " + C + "SET SESSION AUTHORIZATION</code>, advisory locks that depend on connection identity, or " + C + "LISTEN</code>/" + C + "NOTIFY</code>. If your application relies on any of these, test thoroughly before putting Proxy in front of a production PostgreSQL instance."
)
NEW_PROXY_LIM = (
"RDS Proxy for SQL Server authenticates through Secrets Manager — IAM database authentication is not available for SQL Server (it is a MySQL/PostgreSQL-only feature). Known limitations for the SQL Server engine family: Windows (Kerberos/NTLM) authentication is not supported through the proxy, so applications must use SQL authentication with the secret; and some connection-string behaviors differ behind the proxy, so test failover and transaction behavior thoroughly before putting Proxy in front of a production SQL Server instance."
)
reps.append((OLD_PROXY_LIM, NEW_PROXY_LIM))
reps.append((
"Instances where `max_connections` is a bottleneck",
"Instances where connection churn or worker-thread pressure is a bottleneck"
))

# ---- 6.6 ----
reps.append((
"RDS automated backups use EBS volume snapshots plus WAL archiving to enable point-in-time recovery.",
"RDS automated backups use EBS volume snapshots plus transaction log backups to enable point-in-time recovery."
))
reps.append((
"2. Transaction logs (WAL for PostgreSQL, binary logs for MySQL) are continuously uploaded to S3 every 5 minutes.",
"2. Transaction log backups are taken continuously (roughly every 5 minutes) and uploaded to S3."
))
reps.append((
"  --db-instance-class db.r7g.4xlarge " + BS + NL + "  --storage-type gp3 " + BS + NL + "  --multi-az " + BS,
"  --db-instance-class db.r7i.4xlarge " + BS + NL + "  --storage-type gp3 " + BS + NL + "  --multi-az " + BS
))
reps.append((
"  --db-instance-class db.r7g.xlarge " + BS,
"  --db-instance-class db.r7i.xlarge " + BS
))

# ---- 6.7 ----
reps.append((
"In-place major version upgrades on RDS work for some engine combinations (PostgreSQL 14 → 15 → 16 is supported) but not all.",
"In-place major version upgrades on RDS work for some engine combinations (SQL Server 2019 → 2022 is supported) but not all."
))
reps.append((
"For PostgreSQL, in-place upgrade uses `pg_upgrade` underneath. This takes a snapshot first, runs the upgrade, and if it fails, rolls back to the snapshot.",
"For SQL Server, the in-place upgrade runs the SQL Server setup upgrade path underneath. RDS takes a snapshot first, runs the upgrade, and if it fails, rolls back to the snapshot."
))
reps.append((
STR + "Pre-upgrade checklist for PostgreSQL major version upgrade:</strong>",
STR + "Pre-upgrade checklist for a SQL Server major version upgrade:</strong>"
))
OLD_PRE_Q = (
"<code>-- Run these on the CURRENT version before upgrading" + NL +
"-- to identify potential incompatibilities" + NL + NL +
"-- Check for deprecated settings that changed between versions" + NL +
"SELECT name, setting" + NL +
"FROM pg_settings" + NL +
"WHERE name IN (" + NL +
"    'operator_precedence_warning',  -- removed in PG14" + NL +
"    'vacuum_cleanup_index_scale_factor',  -- removed in PG14" + NL +
"    'stats_temp_directory'  -- removed in PG15" + NL +
");"
)
NEW_PRE_Q = (
"<code>-- Run these on the CURRENT version before upgrading" + NL +
"-- to identify potential incompatibilities" + NL + NL +
"-- Check for deprecated features in use (nonzero = in use since last restart)" + NL +
"SELECT object_name, counter_name, cntr_value" + NL +
"FROM sys.dm_os_performance_counters" + NL +
"WHERE object_name LIKE '%Deprecated Features%'" + NL +
"  AND cntr_value &gt; 0;" + NL + NL +
"-- Check database compatibility levels (old levels may block upgrade paths)" + NL +
"SELECT name, compatibility_level" + NL +
"FROM sys.databases" + NL +
"WHERE compatibility_level &lt; 150;" + NL + NL +
"-- Inventory features RDS does not support: linked servers and CLR assemblies" + NL +
"SELECT name, product, provider, data_source" + NL +
"FROM sys.servers" + NL +
"WHERE is_linked = 1;" + NL + NL +
"SELECT name, permission_set_desc" + NL +
"FROM sys.assemblies" + NL +
"WHERE is_user_defined = 1;</code>"
)
reps.append((OLD_PRE_Q, NEW_PRE_Q))
# remove the remaining PG-only queries in the pre-upgrade block
OLD_PRE_Q2 = (
NL + NL +
"-- Check for tables using deprecated data types or features" + NL +
"SELECT " + NL +
"    n.nspname AS schema," + NL +
"    c.relname AS table_name," + NL +
"    a.attname AS column_name," + NL +
"    t.typname AS data_type" + NL +
"FROM pg_attribute a" + NL +
"JOIN pg_class c ON a.attrelid = c.oid" + NL +
"JOIN pg_type t ON a.atttypid = t.oid" + NL +
"JOIN pg_namespace n ON c.relnamespace = n.oid" + NL +
"WHERE t.typname IN ('abstime', 'reltime', 'tinterval')  -- removed in PG12" + NL +
"  AND c.relkind = 'r'" + NL +
"  AND a.attnum &gt; 0;" + NL + NL +
"-- Check for extensions that may not be available in the target version" + NL +
"SELECT name, default_version, installed_version" + NL +
"FROM pg_available_extensions" + NL +
"WHERE installed_version IS NOT NULL" + NL +
"ORDER BY name;" + NL + NL +
"-- Check for any invalid indexes (should be zero before upgrade)" + NL +
"SELECT schemaname, tablename, indexname" + NL +
"FROM pg_indexes" + NL +
"WHERE NOT EXISTS (" + NL +
"    SELECT 1 FROM pg_class c" + NL +
"    JOIN pg_index i ON i.indexrelid = c.oid" + NL +
"    WHERE c.relname = indexname" + NL +
"      AND pg_index_column_has_property(i.indexrelid, 1, 'returnable') IS NOT NULL" + NL +
");</code>"
)
reps.append((OLD_PRE_Q2, "</code>"))
reps.append((
'  --description "Production PostgreSQL 16 parameters" ' + BS,
'  --description "Production SQL Server 2022 parameters" ' + BS
))
reps.append((
"  --db-parameter-group-family postgres16 " + BS,
"  --db-parameter-group-family sqlserver-se-16.0 " + BS
))
reps.append((
"  --engine-version 16.3 " + BS + NL + "  --db-parameter-group-name postgres16-prod " + BS,
"  --engine-version 16.00 " + BS + NL + "  --db-parameter-group-name sqlserver2022-prod " + BS
))

# ---- 6.8 ----
reps.append((
"For PostgreSQL, it leverages " + C + "pg_stat_activity</code> and " + C + "pg_stat_statements</code> internally.",
"For SQL Server, it leverages DMVs such as " + C + "sys.dm_exec_query_stats</code> and " + C + "sys.dm_os_wait_stats</code> internally."
))
OLD_REPLICA_ALARM = (
"# Alarm: Replica lag above 30 seconds" + NL +
"aws cloudwatch put-metric-alarm " + BS + NL +
"  --alarm-name rds-prod-postgres-replica-lag " + BS + NL +
"  --metric-name ReplicaLag " + BS + NL +
"  --namespace AWS/RDS " + BS + NL +
"  --dimensions Name=DBInstanceIdentifier,Value=prod-postgres-replica-01 " + BS + NL +
"  --statistic Maximum " + BS + NL +
"  --period 60 " + BS + NL +
"  --evaluation-periods 3 " + BS + NL +
"  --threshold 30 " + BS + NL +
"  --comparison-operator GreaterThanThreshold " + BS + NL +
"  --alarm-actions arn:aws:sns:us-east-1:123456789012:db-alerts " + BS + NL +
"  --region us-east-1"
)
NEW_MEM_ALARM = (
"<code># Alarm: Freeable memory below 2 GB (memory pressure / buffer pool squeeze)" + NL +
"aws cloudwatch put-metric-alarm " + BS + NL +
"  --alarm-name rds-prod-sql-low-memory " + BS + NL +
"  --metric-name FreeableMemory " + BS + NL +
"  --namespace AWS/RDS " + BS + NL +
"  --dimensions Name=DBInstanceIdentifier,Value=prod-sql-primary " + BS + NL +
"  --statistic Average " + BS + NL +
"  --period 300 " + BS + NL +
"  --evaluation-periods 2 " + BS + NL +
"  --threshold 2147483648 " + BS + NL +
"  --comparison-operator LessThanThreshold " + BS + NL +
"  --alarm-actions arn:aws:sns:us-east-1:123456789012:db-alerts " + BS + NL +
"  --region us-east-1</code>"
)
reps.append((OLD_REPLICA_ALARM, NEW_MEM_ALARM))

# ---- takeaways ----
reps.append((
"**Instance family selection matters more than raw size.** Graviton (g-suffix) instances offer better price-performance for PostgreSQL and MySQL, while SQL Server and Oracle require Intel or AMD families. Never use T-series burstable instances for production OLTP workloads that sustain CPU pressure — CPU credit exhaustion causes silent, unpredictable throttling.",
"**Instance family selection matters more than raw size.** Graviton (g-suffix) instances do not support SQL Server at all — for RDS for SQL Server always choose Intel families (db.r7i, db.m7i). Never use T-series burstable instances for production OLTP workloads that sustain CPU pressure — CPU credit exhaustion causes silent, unpredictable throttling."
))
reps.append((
"**Multi-AZ and Read Replicas solve different problems and are not interchangeable.** Multi-AZ provides synchronous failover with near-zero RPO but the standby cannot serve reads. Read Replicas provide asynchronous read scaling and cross-region DR but have replication lag and do not auto-failover. Production architectures typically need both: a Multi-AZ primary with Read Replicas for workload offloading.",
"**Multi-AZ is failover, not read scaling — and RDS for SQL Server has no read replicas.** Multi-AZ provides synchronous failover with near-zero RPO but the secondary cannot serve reads. Plan read scaling explicitly: readable Always On secondaries on EC2, or snapshot-refreshed reporting copies. Production architectures pair a Multi-AZ primary with a deliberate read-offload strategy."
))

# ---- global identifier sweeps (after block replacements) ----
t2 = t
for old, new in reps:
    n = t2.count(old)
    if n == 1:
        t2 = t2.replace(old, new)
    else:
        print("FAILED count=" + str(n) + ": " + old[:90])
        sys.exit(1)
t = t2

sweeps = [
    ("--db-parameter-group-name postgres16-prod", "--db-parameter-group-name sqlserver2022-prod"),
    ("pre-upgrade-pg15-to-pg16", "pre-upgrade-sql2019-to-sql2022"),
    ("prod-postgres-primary", "prod-sql-primary"),
    ("prod-postgres-01", "prod-sql-01"),
    ("prod-postgres-recovered-20240115", "prod-sql-recovered-20240115"),
    ("prod-postgres-before-migration-20240115", "prod-sql-before-migration-20240115"),
    ("staging-postgres-from-prod-snap", "staging-sql-from-prod-snap"),
    ("rds-prod-postgres-", "rds-prod-sql-"),
    ("db.r7g.", "db.r7i."),
    ('--log-stream-name-prefix "prod-postgres-primary"', '--log-stream-name-prefix "prod-sql-primary"'),
]
for old, new in sweeps:
    t = t.replace(old, new)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch06-C OK:", len(reps), "replacements +", len(sweeps), "sweeps")
