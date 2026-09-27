#!/usr/bin/env python3
"""Rewrite PostgreSQL-centric content in b5-ch04 to SQL Server focus (v2, raw HTML)."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch04-cloud-dba-role.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'
reps = []

reps.append((
f"""On RDS for PostgreSQL, you will never run <code {CODE}>apt-get upgrade postgresql</code>, restart the OS, or access <code {CODE}>/var/lib/postgresql</code> directly. AWS handles minor version patching on a schedule you influence but do not fully control unless you disable auto minor version upgrades explicitly.""",
f"""On RDS for SQL Server, you will never run Windows Update on the host, restart the OS, or access the SQL Server installation directories directly. AWS handles patching on a schedule you influence but do not fully control unless you take explicit ownership of the maintenance window."""
))
reps.append((
f"""On-premises PostgreSQL access control flows through two files: <code {CODE}>postgresql.conf</code> controls what the engine does, and <code {CODE}>pg_hba.conf</code> controls who can connect, from where, and with what authentication method. SQL Server uses logins, server roles, and Windows Authentication through Active Directory. In the cloud, these familiar mechanisms are extended — not replaced — by identity and access management layers that sit above the database engine.""",
f"""On-premises SQL Server access control flows through two layers: server logins control who can connect, and database users and roles control what they can do once connected. Windows Authentication through Active Directory ties both layers to corporate identity. In the cloud, these familiar mechanisms are extended — not replaced — by identity and access management layers that sit above the database engine."""
))
reps.append((
"""# Enable IAM authentication on an existing RDS PostgreSQL instance
aws rds modify-db-instance \\
  --db-instance-identifier prod-postgres-01 \\
  --enable-iam-database-authentication \\
  --apply-immediately

# Generate an authentication token for a database user named "app_user"
aws rds generate-db-auth-token \\
  --hostname prod-postgres-01.cxyz1234.us-east-1.rds.amazonaws.com \\
  --port 5432 \\
  --region us-east-1 \\
  --username app_user</code></pre>""",
"""# Enable IAM authentication on an existing RDS for SQL Server instance
aws rds modify-db-instance \\
  --db-instance-identifier prod-sql-01 \\
  --enable-iam-database-authentication \\
  --apply-immediately

# Generate an authentication token for a login named "app_user"
aws rds generate-db-auth-token \\
  --hostname prod-sql-01.cxyz1234.us-east-1.rds.amazonaws.com \\
  --port 1433 \\
  --region us-east-1 \\
  --username app_user</code></pre>"""
))
reps.append((
f"""On the database side, the user must exist with the <code {CODE}>rds_iam</code> role granted:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- Create a database user that authenticates via IAM
CREATE USER app_user WITH LOGIN;
GRANT rds_iam TO app_user;

-- The user has no password — authentication is entirely token-based""",
f"""On the database side, the login must exist on the instance and be associated with the IAM role:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- Create the login for the application service account.
-- Keep a strong Secrets Manager-backed password as a break-glass fallback;
-- day-to-day authentication is token-based and never uses the static password.
CREATE LOGIN [app_user] WITH PASSWORD = '<managed-by-secrets-manager>';"""
))
reps.append((
f"""On self-managed PostgreSQL, you edit <code {CODE}>postgresql.conf</code> directly and control every engine parameter from <code {CODE}>max_connections</code> to <code {CODE}>wal_level</code> to <code {CODE}>autovacuum_vacuum_cost_delay</code>. On RDS, that file is owned by AWS. You configure the engine through Parameter Groups — a named collection of engine parameters that you apply to one or more DB instances.""",
f"""On self-managed SQL Server, you run <code {CODE}>sp_configure</code> directly and control every engine setting from <code {CODE}>max server memory (MB)</code> to <code {CODE}>cost threshold for parallelism</code> to <code {CODE}>fill factor (%)</code>. On RDS, that surface is owned by AWS. You configure the engine through Parameter Groups — a named collection of engine parameters that you apply to one or more DB instances."""
))
reps.append((
"""# Create a custom parameter group for RDS PostgreSQL 15
aws rds create-db-parameter-group \\
  --db-parameter-group-name prod-pg15-custom \\
  --db-parameter-group-family postgres15 \\
  --description "Production PostgreSQL 15 tuning"

# Modify key parameters
aws rds modify-db-parameter-group \\
  --db-parameter-group-name prod-pg15-custom \\
  --parameters \\
    "ParameterName=shared_buffers,ParameterValue={DBInstanceClassMemory/4},ApplyMethod=pending-reboot" \\
    "ParameterName=work_mem,ParameterValue=65536,ApplyMethod=immediate" \\
    "ParameterName=autovacuum_vacuum_scale_factor,ParameterValue=0.01,ApplyMethod=immediate" \\
    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate"

# Associate with an instance
aws rds modify-db-instance \\
  --db-instance-identifier prod-postgres-01 \\
  --db-parameter-group-name prod-pg15-custom \\
  --apply-immediately</code></pre>""",
"""# Create a custom parameter group for RDS SQL Server 2022
aws rds create-db-parameter-group \\
  --db-parameter-group-name prod-sql2022-custom \\
  --db-parameter-group-family sqlserver-se-16.0 \\
  --description "Production SQL Server 2022 tuning"

# Modify key parameters
aws rds modify-db-parameter-group \\
  --db-parameter-group-name prod-sql2022-custom \\
  --parameters \\
    "ParameterName=max server memory (MB),ParameterValue={DBInstanceClassMemory/1048576}*3/4,ApplyMethod=pending-reboot" \\
    "ParameterName=cost threshold for parallelism,ParameterValue=50,ApplyMethod=immediate" \\
    "ParameterName=max degree of parallelism,ParameterValue=8,ApplyMethod=immediate" \\
    "ParameterName=fill factor (%),ParameterValue=90,ApplyMethod=pending-reboot" \\
    "ParameterName=optimize for ad hoc workloads,ParameterValue=1,ApplyMethod=immediate"

# Associate with an instance
aws rds modify-db-instance \\
  --db-instance-identifier prod-sql-01 \\
  --db-parameter-group-name prod-sql2022-custom \\
  --apply-immediately</code></pre>"""
))
reps.append((
f"""Note the formula syntax for <code {CODE}>shared_buffers</code>. RDS supports arithmetic expressions using <code {CODE}>{{DBInstanceClassMemory}}</code> as a variable — this is how AWS recommends setting memory-relative parameters so the configuration remains valid if you resize the instance class. For a <code {CODE}>db.r6g.2xlarge</code> with 64 GB RAM, <code {CODE}>{{DBInstanceClassMemory/4}}</code> evaluates to 16 GB, which is 25% of RAM — the standard PostgreSQL recommendation.""",
f"""Note the formula syntax for <code {CODE}>max server memory (MB)</code>. RDS supports arithmetic expressions using <code {CODE}>{{DBInstanceClassMemory}}</code> as a variable — this is how AWS recommends setting memory-relative parameters so the configuration remains valid if you resize the instance class. For a <code {CODE}>db.r6i.2xlarge</code> with 64 GB RAM, leaving roughly a quarter of memory for the OS is the standard SQL Server practice, which the formula encodes directly."""
))
reps.append((
"""<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> `wal_level` is not directly settable on RDS PostgreSQL — it defaults to `replica` and only moves to `logical` when you enable the `rds.logical_replication` parameter (which requires a reboot); you cannot control it independently of that flag</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> `archive_mode` is managed by AWS; you cannot disable it without understanding it breaks PITR</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> `listen_addresses` is managed by AWS</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> `ssl` is forced on — you cannot disable SSL on RDS connections</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> `superuser` access does not exist on RDS; the `rds_superuser` role is a functional substitute but does not grant OS-level access</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> Extensions must be whitelisted by AWS; you cannot install arbitrary shared libraries</li>""",
"""<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> Many `sp_configure` options are restricted to the curated set AWS exposes; arbitrary trace flags and startup parameters are unavailable</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> Transaction log backup scheduling is managed by AWS; you cannot run your own log backup chain on the instance</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> Network protocols and endpoints are managed by AWS</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> TLS is forced on — you cannot disable encryption on RDS connections</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> `sysadmin` access does not exist on RDS; the master user is a functional substitute but does not grant OS-level access</li>
<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> Components must be on the supported list — no SQL Server Agent, no SSIS, SSAS, or SSRS</li>"""
))
reps.append((
f"""On-premises DBAs typically own their full monitoring stack — Prometheus with pg_exporter, Datadog agents, custom scripts querying <code {CODE}>pg_stat_activity</code>, <code {CODE}>pg_stat_bgwriter</code>, and <code {CODE}>pg_locks</code>. In the cloud, the provider delivers a baseline monitoring layer automatically, and the DBA's job shifts from building that layer to interpreting it, extending it, and setting appropriate thresholds.""",
f"""On-premises DBAs typically own their full monitoring stack — Datadog agents, custom scripts querying <code {CODE}>sys.dm_exec_requests</code>, <code {CODE}>sys.dm_os_wait_stats</code>, and <code {CODE}>sys.dm_tran_locks</code>. In the cloud, the provider delivers a baseline monitoring layer automatically, and the DBA's job shifts from building that layer to interpreting it, extending it, and setting appropriate thresholds."""
))
reps.append((
f"""For a production workload investigation, Performance Insights replaces the manual practice of sampling <code {CODE}>pg_stat_activity</code> every few seconds and correlating the results. The UI presents a visual timeline of database load against the max_vCPUs line — anything above that line indicates the database is CPU-bound or waiting on a bottleneck that requires investigation.""",
f"""For a production workload investigation, Performance Insights replaces the manual practice of sampling <code {CODE}>sys.dm_exec_requests</code> every few seconds and correlating the results. The UI presents a visual timeline of database load against the max_vCPUs line — anything above that line indicates the database is CPU-bound or waiting on a bottleneck that requires investigation."""
))
reps.append((
f"""*Instance sizing and Reserved Instances.* On-demand pricing for a <code {CODE}>db.r6g.2xlarge</code> running Aurora PostgreSQL in us-east-1 is meaningful at monthly scale.""",
f"""*Instance sizing and Reserved Instances.* On-demand pricing for a <code {CODE}>db.r7g.2xlarge</code> running Aurora MySQL in us-east-1 is meaningful at monthly scale."""
))
reps.append((
"""<strong class="text-white">Query optimization does not change.</strong> EXPLAIN and EXPLAIN ANALYZE on RDS PostgreSQL produce the same output as on self-managed PostgreSQL. The same principles govern index selection, join ordering, statistics quality, and plan regression. Query Store on Azure SQL and Performance Insights on RDS give you better visibility into query behavior than most on-premises deployments had, but interpreting that data requires the same foundational knowledge of execution plans and cost estimation.""",
"""<strong class="text-white">Query optimization does not change.</strong> Actual execution plans on RDS for SQL Server are produced by the same optimizer as on self-managed SQL Server. The same principles govern index selection, join ordering, statistics quality, and plan regression. Query Store on Azure SQL and Performance Insights on RDS give you better visibility into query behavior than most on-premises deployments had, but interpreting that data requires the same foundational knowledge of execution plans and cost estimation."""
))
reps.append((
f"""<strong class="text-white">Backup and recovery reasoning does not change.</strong> The mechanics of backup change — you do not run <code {CODE}>pg_basebackup</code> manually on RDS, and you do not schedule SQL Server maintenance plan jobs on Azure SQL.""",
f"""<strong class="text-white">Backup and recovery reasoning does not change.</strong> The mechanics of backup change — you do not run <code {CODE}>BACKUP DATABASE</code> manually on RDS for SQL Server, and you do not schedule SQL Server maintenance plan jobs on Azure SQL."""
))
reps.append((
f"""<strong class="text-white">Locking and concurrency design does not change.</strong> Advisory locks, row-level locking, table-level locking, deadlock detection — these behave identically. The cloud DBA who knows how to diagnose a lock contention issue using <code {CODE}>pg_locks</code> and <code {CODE}>pg_stat_activity</code> on self-managed PostgreSQL will apply exactly the same skills on RDS.""",
f"""<strong class="text-white">Locking and concurrency design does not change.</strong> Application locks via <code {CODE}>sp_getapplock</code>, row-level locking, table-level locking, deadlock detection — these behave identically. The cloud DBA who knows how to diagnose a lock contention issue using <code {CODE}>sys.dm_tran_locks</code> and <code {CODE}>sys.dm_exec_requests</code> on self-managed SQL Server will apply exactly the same skills on RDS."""
))

failed = []
for old, new in reps:
    n = t.count(old)
    if n == 1:
        t = t.replace(old, new)
    else:
        failed.append((n, old[:90]))

# Global mechanical renames (all occurrences)
globals_ = [
    ("--db-instance-identifier prod-postgres-01 \\", "--db-instance-identifier prod-sql-01 \\"),
    ("Name=DBInstanceIdentifier,Value=prod-postgres-reader-1", "Name=DBInstanceIdentifier,Value=prod-sql-reader-1"),
]
for old, new in globals_:
    t = t.replace(old, new)

if failed:
    print("FAILED REPLACEMENTS:")
    for n, s in failed:
        print(f"  count={n}: {s}")
    sys.exit(1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch04 OK:", len(reps), "paragraph replacements +", len(globals_), "global renames applied")
