#!/usr/bin/env python3
"""Rewrite PostgreSQL-centric content in b5-ch01 to SQL Server focus."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch01-cloud-shift.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

reps = []

# 1. Intro paragraph
reps.append((
"""If you have spent years managing PostgreSQL clusters on bare metal, tuning SQL Server on VMware, or babysitting Oracle RAC through a 2 AM failover, this chapter is your orientation briefing.""",
"""If you have spent years managing SQL Server failover clusters on bare metal, tuning instances on VMware, or babysitting Always On availability groups through a 2 AM failover, this chapter is your orientation briefing."""
))

# 2. 1.1 on-premises stack paragraph
reps.append((
"""When you managed an on-premises PostgreSQL 14 cluster, you owned the entire stack. You decided the kernel version, the filesystem (XFS over ext4 for most serious shops), the storage controller queue depth, the NIC bonding configuration, and the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">vm.swappiness</code> setting. You wrote the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">postgresql.conf</code>. You managed <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_hba.conf</code> line by line. Failure meant your pager went off. Victory meant the database stayed up without anyone noticing.""",
"""When you managed an on-premises SQL Server 2022 cluster, you owned the entire stack. You decided the Windows Server build, the disk layout (data, log, tempdb, and backup volumes on separate LUNs), the storage controller queue depth, the NIC teaming configuration, and the power plan. You configured startup parameters and trace flags in SQL Server Configuration Manager. You managed logins, server roles, and endpoint permissions line by line. Failure meant your pager went off. Victory meant the database stayed up without anyone noticing."""
))

# 3. Boundary paragraph
reps.append((
"""That boundary is different on every platform, and it shifts with every major release. On RDS for PostgreSQL, you cannot modify kernel parameters like <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">kernel.shmmax</code> or use <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_prewarm</code> to manually warm the buffer cache after a failover — the OS is not yours. On Azure SQL Database, you cannot access the underlying SQL Server instance with a sysadmin login the way you would on a self-managed instance. On Cloud SQL, you cannot install custom extensions not on Google's approved list.""",
"""That boundary is different on every platform, and it shifts with every major release. On RDS for SQL Server, you cannot set startup parameters or trace flags the way you would in SQL Server Configuration Manager — only the options and parameters AWS exposes through parameter groups and option groups are available, and SQL Server Agent is not offered at all. On Azure SQL Database, you cannot access the underlying SQL Server instance with a sysadmin login the way you would on a self-managed instance. On Cloud SQL for SQL Server, you cannot use features that require OS-level access, and job scheduling has to move off SQL Server Agent to Cloud Scheduler."""
))

# 4. Backups paragraph (WAL/pg_basebackup)
reps.append((
"""<strong class="text-white">Backups</strong> are automated, with point-in-time recovery available up to the retention period you configure (1–35 days on RDS, 1–35 days on Azure SQL, 1–35 days on Cloud SQL). The backup mechanism itself is managed — on RDS, automated backups use storage-level snapshots combined with continuous WAL archiving to S3. You do not run <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_basebackup</code> manually. You do not manage WAL archiving with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">archive_command</code>. You configure a retention period and trust the service.""",
"""<strong class="text-white">Backups</strong> are automated, with point-in-time recovery available up to the retention period you configure (1–35 days on RDS, 1–35 days on Azure SQL, 1–35 days on Cloud SQL). The backup mechanism itself is managed — on RDS for SQL Server, automated backups combine storage-level snapshots with continuous transaction log uploads to S3. You do not run <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">BACKUP DATABASE</code> manually. You do not schedule your own log backups or manage log shipping. You configure a retention period and trust the service."""
))

# 5. 1.3 config model intro
reps.append((
"""On-premises PostgreSQL is configured through <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">postgresql.conf</code> and <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_hba.conf</code>. SQL Server is configured through <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure</code>, trace flags, and the SQL Server Configuration Manager. When you move to managed databases, these familiar mechanisms are replaced by provider-specific configuration abstractions.""",
"""On-premises SQL Server is configured through <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure</code>, trace flags, startup parameters, and the SQL Server Configuration Manager. When you move to managed databases, these familiar mechanisms are replaced by provider-specific configuration abstractions — parameter groups, option groups, database flags, and database-scoped configurations."""
))

# 6. RDS parameter groups paragraph
reps.append((
"""<strong class="text-white">AWS RDS Parameter Groups</strong> are collections of engine parameters that you apply to one or more DB instances. They map almost directly to <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">postgresql.conf</code> for RDS PostgreSQL, or to SQL Server instance-level configuration for RDS SQL Server. Some parameters are static (requiring a reboot to apply), and some are dynamic (applied immediately). The critical difference from on-premises is that some parameters are locked entirely — you cannot set <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">wal_level = logical</code> on standard RDS PostgreSQL without enabling logical replication at the instance level through a separate parameter, and even then, the implementation is managed rather than raw.""",
"""<strong class="text-white">AWS RDS Parameter Groups</strong> are collections of engine parameters that you apply to one or more DB instances. For RDS for SQL Server they map to the instance-level settings you would normally change with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure</code> — max server memory, cost threshold for parallelism, max degree of parallelism, fill factor, and the like. Some parameters are static (requiring a reboot to apply), and some are dynamic (applied immediately). The critical difference from on-premises is that some capabilities are locked entirely — you cannot add arbitrary trace flags or startup parameters, and several features (SQL Server Agent, replication publisher roles, native linked-server providers beyond the supported set) are simply unavailable on the managed surface."""
))

# 7. Parameter group CLI lead-in + code block -> RDS SQL Server
reps.append((
"""Here is how you create and apply a custom parameter group for RDS PostgreSQL using the AWS CLI:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Create a custom parameter group for PostgreSQL 15
aws rds create-db-parameter-group \\
  --db-parameter-group-name prod-pg15-tuned \\
  --db-parameter-group-family postgres15 \\
  --description "Production PostgreSQL 15 tuned parameters" \\
  --region us-east-1

# Set shared_buffers — note: on RDS this is set as a percentage
# of instance memory using DBInstanceClassMemory formula
aws rds modify-db-parameter-group \\
  --db-parameter-group-name prod-pg15-tuned \\
  --parameters \\
    "ParameterName=shared_buffers,ParameterValue={DBInstanceClassMemory/32768},ApplyMethod=pending-reboot" \\
    "ParameterName=work_mem,ParameterValue=65536,ApplyMethod=immediate" \\
    "ParameterName=max_connections,ParameterValue=500,ApplyMethod=pending-reboot" \\
    "ParameterName=checkpoint_completion_target,ParameterValue=0.9,ApplyMethod=immediate" \\
    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate" \\
  --region us-east-1

# Apply the parameter group to an existing RDS instance
aws rds modify-db-instance \\
  --db-instance-identifier prod-postgres-primary \\
  --db-parameter-group-name prod-pg15-tuned \\
  --apply-immediately \\
  --region us-east-1</code></pre>

<p class="text-gray-300 leading-relaxed">Notice the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">{DBInstanceClassMemory/32768}</code> formula. RDS does not let you set <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">shared_buffers</code> in absolute kilobytes the way you would in <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">postgresql.conf</code>. Instead, it uses a formula language that resolves against the actual memory of whatever instance class the parameter group is applied to. This is actually a feature — the parameter group becomes portable across instance sizes without manual recalculation — but it is a mental model shift if you are used to typing <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">shared_buffers = 8GB</code> directly.</p>""",
"""Here is how you create and apply a custom parameter group for RDS for SQL Server using the AWS CLI:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Create a custom parameter group for SQL Server 2022 (Standard Edition)
aws rds create-db-parameter-group \\
  --db-parameter-group-name prod-sql2022-tuned \\
  --db-parameter-group-family sqlserver-se-16.0 \\
  --description "Production SQL Server 2022 tuned parameters" \\
  --region us-east-1

# Tune the settings you would normally change with sp_configure.
# RDS supports a formula language ({DBInstanceClassMemory/...}) so the
# parameter group stays portable across instance classes.
aws rds modify-db-parameter-group \\
  --db-parameter-group-name prod-sql2022-tuned \\
  --parameters \\
    "ParameterName=max server memory (MB),ParameterValue={DBInstanceClassMemory/1048576}*3/4,ApplyMethod=pending-reboot" \\
    "ParameterName=cost threshold for parallelism,ParameterValue=50,ApplyMethod=immediate" \\
    "ParameterName=max degree of parallelism,ParameterValue=8,ApplyMethod=immediate" \\
    "ParameterName=fill factor (%),ParameterValue=90,ApplyMethod=pending-reboot" \\
    "ParameterName=optimize for ad hoc workloads,ParameterValue=1,ApplyMethod=immediate" \\
  --region us-east-1

# Apply the parameter group to an existing RDS for SQL Server instance
aws rds modify-db-instance \\
  --db-instance-identifier prod-sql-primary \\
  --db-parameter-group-name prod-sql2022-tuned \\
  --apply-immediately \\
  --region us-east-1</code></pre>

<p class="text-gray-300 leading-relaxed">Notice the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">{DBInstanceClassMemory/1048576}</code> formula. RDS resolves these formulas against the actual memory of whatever instance class the parameter group is applied to. This is actually a feature — the parameter group becomes portable across instance sizes without manual recalculation — but it is a mental model shift if you are used to running <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure 'max server memory (MB)', 98304; RECONFIGURE;</code> with a hard-coded number on each host.</p>"""
))

# 8. Azure parameters paragraph + CLI -> SQL Server focus
reps.append((
"""<strong class="text-white">Azure SQL Server Parameters</strong> live in the Azure Portal under "Server parameters" for Azure Database for PostgreSQL Flexible Server, or as database-scoped configurations for Azure SQL Database (the managed SQL Server service). The CLI equivalent:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Azure CLI: Configure parameters on Azure Database for PostgreSQL Flexible Server
az postgres flexible-server parameter set \\
  --resource-group prod-rg \\
  --server-name prod-postgres-flex \\
  --name work_mem \\
  --value 65536

az postgres flexible-server parameter set \\
  --resource-group prod-rg \\
  --server-name prod-postgres-flex \\
  --name log_min_duration_statement \\
  --value 1000

# For Azure SQL Database (SQL Server-compatible), use database-scoped configs
# Connect with sqlcmd or SSMS and run:
# ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP = 4;
# ALTER DATABASE SCOPED CONFIGURATION SET LEGACY_CARDINALITY_ESTIMATION = OFF;</code></pre>""",
"""<strong class="text-white">Azure SQL configuration</strong> splits into two layers. For Azure SQL Managed Instance, server-level settings are managed through the portal or the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">az sql mi</code> CLI; for Azure SQL Database, most tuning happens through database-scoped configurations run as T-SQL. The CLI and T-SQL equivalents:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Azure CLI: list server configuration options on a Managed Instance
az sql mi show \\
  --resource-group prod-rg \\
  --name prod-sqlmi \\
  --query "{vCores: vCores, storageSizeInGB: storageSizeInGB, licenseType: licenseType}"

# For Azure SQL Database, use database-scoped configurations (via sqlcmd or SSMS)
# -- set parallelism and cardinality estimator behavior per database:
# ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP = 4;
# ALTER DATABASE SCOPED CONFIGURATION SET LEGACY_CARDINALITY_ESTIMATION = OFF;
# ALTER DATABASE SCOPED CONFIGURATION SET QUERY_OPTIMIZER_HOTFIXES = ON;

# Query Store is on by default on Azure SQL Database — configure retention:
# ALTER DATABASE [production] SET QUERY_STORE
#   (OPERATION_MODE = READ_WRITE, CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30));</code></pre>"""
))

# 9. GCP flags paragraph -> Cloud SQL for SQL Server
reps.append((
"""<strong class="text-white">Google Cloud SQL and AlloyDB</strong> use database flags, which are passed at instance creation or modification time:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># GCP CLI: Set database flags on a Cloud SQL PostgreSQL instance
gcloud sql instances patch prod-postgres-instance \\
  --database-flags \\
    max_connections=500,\\
    work_mem=65536,\\
    log_min_duration_statement=1000,\\
    checkpoint_completion_target=0.9 \\
  --project my-prod-project

# Some flags require an instance restart — gcloud will warn you
# Check which flags are supported and whether restart is needed
gcloud sql instances describe prod-postgres-instance \\
  --project my-prod-project \\
  --format="json(settings.databaseFlags)"</code></pre>""",
"""<strong class="text-white">Google Cloud SQL</strong> uses database flags, which are passed at instance creation or modification time. Cloud SQL for SQL Server exposes a much smaller flag surface than the PostgreSQL offering — most SQL Server tuning on GCP happens through the console or <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure</code> inside the instance:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># GCP CLI: Set database flags on a Cloud SQL for SQL Server instance
gcloud sql instances patch prod-sql-instance \\
  --database-flags \\
    max degree of parallelism=4 \\
  --project my-prod-project

# Some flags require an instance restart — gcloud will warn you
# Check which flags are supported and whether restart is needed
gcloud sql instances describe prod-sql-instance \\
  --project my-prod-project \\
  --format="json(settings.databaseFlags)"

# Everything else is T-SQL inside the instance, e.g.:
# EXEC sp_configure 'cost threshold for parallelism', 50; RECONFIGURE;</code></pre>"""
))

# 10. Gotcha paragraph
reps.append((
"""A production gotcha shared across all three platforms: you will encounter parameters that exist on-premises but are either locked, unavailable, or behave differently in managed environments. On RDS PostgreSQL, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">max_wal_size</code> cannot be set below a minimum enforced by AWS. On Cloud SQL, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">fsync</code> cannot be disabled even if you wanted to (which you do not). On Azure SQL Database (the SQL Server service), you cannot use <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">DBCC FREEPROCCACHE</code> without specific permissions, and <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">DBCC DROPCLEANBUFFERS</code> is not available at all in the serverless tier.""",
"""A production gotcha shared across all three platforms: you will encounter settings that exist on-premises but are either locked, unavailable, or behave differently in managed environments. On RDS for SQL Server, only a curated subset of <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure</code> options are exposed, and features like SQL Server Agent and replication publisher roles are unavailable entirely. On Cloud SQL for SQL Server, cross-database queries and linked servers have restrictions you would never hit on a self-managed instance. On Azure SQL Database, you cannot use <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">DBCC FREEPROCCACHE</code> without specific permissions, and <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">DBCC DROPCLEANBUFFERS</code> is not available at all in the serverless tier."""
))

# 11. 1.4 heading + networking paragraph
reps.append((
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">1.4 Networking and Security: The New pg_hba.conf</h3>

<p class="text-gray-300 leading-relaxed">The most jarring transition for on-premises DBAs is often not the configuration model — it is the networking and authentication model. On-premises, your security perimeter is relatively straightforward: <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_hba.conf</code> controls who can connect to PostgreSQL, firewall rules at the OS or network level control which IPs can reach port 5432, and SSL is configured in <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">postgresql.conf</code> with certificates you manage yourself.</p>""",
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">1.4 Networking and Security: The New Perimeter</h3>

<p class="text-gray-300 leading-relaxed">The most jarring transition for on-premises DBAs is often not the configuration model — it is the networking and authentication model. On-premises, your security perimeter is relatively straightforward: SQL Server logins and Windows authentication control who can connect, Windows Firewall or network ACLs control which IPs can reach port 1433, and TLS is configured in SQL Server Configuration Manager with certificates you manage yourself.</p>"""
))

# 12. create-db-instance code block -> SQL Server
reps.append((
"""aws rds create-db-instance \\
  --db-instance-identifier prod-postgres-primary \\
  --db-instance-class db.r6g.2xlarge \\
  --engine postgres \\
  --engine-version 15.4 \\
  --master-username dbadmin \\
  --master-user-password "$(aws secretsmanager get-secret-value \\
      --secret-id prod/postgres/master-password \\
      --query SecretString --output text)" \\""",
"""aws rds create-db-instance \\
  --db-instance-identifier prod-sql-primary \\
  --db-instance-class db.r6i.2xlarge \\
  --engine sqlserver-se \\
  --engine-version 16.00 \\
  --master-username dbadmin \\
  --master-user-password "$(aws secretsmanager get-secret-value \\
      --secret-id prod/sqlserver/master-password \\
      --query SecretString --output text)" \\"""
))

# 13. IAM auth paragraph (pg_hba mention)
reps.append((
"""database users are mapped to IAM roles, and the authentication token is generated on the fly with a 15-minute validity window. No long-lived passwords stored in application config files. What you used to manage in <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_hba.conf</code> with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">md5</code> or <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">scram-sha-256</code> authentication lines, you now manage with IAM policies.""",
"""database users are mapped to IAM roles, and the authentication token is generated on the fly with a 15-minute validity window. No long-lived passwords stored in application config files. What you used to manage with SQL Server logins, contained database users, and Windows authentication groups on-premises, you now manage with IAM policies and the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">rds_iam_roles</code> mapping."""
))

# 14. Python IAM code block -> pyodbc / SQL Server
reps.append((
"""<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Python: Generate an IAM auth token and connect to RDS PostgreSQL
import boto3
import psycopg2
from botocore.exceptions import ClientError

def get_rds_iam_token(hostname: str, port: int, username: str, region: str) -&gt; str:
    \"\"\"Generate a short-lived IAM authentication token for RDS.\"\"\"
    client = boto3.client('rds', region_name=region)
    token = client.generate_db_auth_token(
        DBHostname=hostname,
        Port=port,
        DBUsername=username,
        Region=region
    )
    return token

def connect_with_iam_auth():
    hostname = "prod-postgres-primary.cluster-xxxxxxxxxxxx.us-east-1.rds.amazonaws.com"
    port = 5432
    username = "app_readonly"
    region = "us-east-1"
    database = "production"

    # Token is valid for 15 minutes — generate fresh per connection
    token = get_rds_iam_token(hostname, port, username, region)

    conn = psycopg2.connect(
        host=hostname,
        port=port,
        user=username,
        password=token,
        database=database,
        sslmode="verify-full",
        sslrootcert="/etc/ssl/certs/rds-ca-2019-root.pem"
    )
    return conn

# The IAM role attached to the EC2/Lambda/ECS task must have:
# rds-db:connect permission on the specific DB user resource ARN
# arn:aws:rds-db:us-east-1:123456789012:dbuser:prod-postgres-primary/app_readonly</code></pre>""",
"""<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Python: Generate an IAM auth token and connect to RDS for SQL Server
import boto3
import pyodbc
from botocore.exceptions import ClientError

def get_rds_iam_token(hostname: str, port: int, username: str, region: str) -&gt; str:
    \"\"\"Generate a short-lived IAM authentication token for RDS.\"\"\"
    client = boto3.client('rds', region_name=region)
    token = client.generate_db_auth_token(
        DBHostname=hostname,
        Port=port,
        DBUsername=username,
        Region=region
    )
    return token

def connect_with_iam_auth():
    hostname = "prod-sql-primary.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com"
    port = 1433
    username = "app_readonly"
    region = "us-east-1"
    database = "production"

    # Token is valid for 15 minutes — generate fresh per connection
    token = get_rds_iam_token(hostname, port, username, region)

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={hostname},{port};DATABASE={database};"
        f"UID={username};PWD={token};Encrypt=yes;"
        f"TrustServerCertificate=no"
    )
    return pyodbc.connect(conn_str)

# The IAM role attached to the EC2/Lambda/ECS task must have:
# rds-db:connect permission on the specific DB user resource ARN
# arn:aws:rds-db:us-east-1:123456789012:dbuser:prod-sql-primary/app_readonly
#
# NOTE: the SQL Server login must already exist on the instance and be
# mapped to the IAM role — IAM auth does not create logins for you.</code></pre>"""
))

# 15. 1.5 observability intro paragraph
reps.append((
"""On a self-managed PostgreSQL server, your observability toolkit is <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_activity</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_statements</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_bgwriter</code>, the PostgreSQL log files, and whatever you have wired up with Prometheus and Grafana. On SQL Server, it is DMVs, Extended Events, and SQL Server Profiler. You own the data collection pipeline end to end.""",
"""On a self-managed SQL Server instance, your observability toolkit is the dynamic management views (<code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_requests</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_query_stats</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_os_wait_stats</code>), Extended Events, Query Store, the SQL Server error log, and whatever you have wired up with Prometheus and Grafana. You own the data collection pipeline end to end."""
))

# 16. 1.5 heading
reps.append((
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">1.5 Operational Observability: From pg_stat to CloudWatch and Beyond</h3>""",
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">1.5 Operational Observability: From DMVs to CloudWatch and Beyond</h3>"""
))

# 17. CloudWatch alarm dimensions
reps.append((
"""  --dimensions Name=DBInstanceIdentifier,Value=prod-postgres-primary \\""",
"""  --dimensions Name=DBInstanceIdentifier,Value=prod-sql-primary \\"""
))
reps.append((
"""  --dimensions Name=DBInstanceIdentifier,Value=prod-postgres-replica-1 \\""",
"""  --dimensions Name=DBInstanceIdentifier,Value=prod-sql-replica-1 \\"""
))

# 18. Performance Insights paragraph
reps.append((
"""Performance Insights, available on RDS and Aurora, is the closest cloud equivalent to <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_statements</code> combined with a wait event analysis tool. It shows you top SQL by load, broken down by wait events (CPU, I/O, lock, etc.), across a 7-day free window or up to 2 years with the paid tier. For most production workload analysis, it replaces the combination of <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_statements</code> reset cycles and manual wait event querying you ran on-premises.""",
"""Performance Insights, available on RDS and Aurora, is the closest cloud equivalent to querying <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_query_stats</code> joined to a wait-statistics analysis. It shows you top SQL by load, broken down by wait events (CPU, I/O, lock, etc.), across a 7-day free window or up to 2 years with the paid tier. For most production workload analysis, it replaces the combination of periodic DMV snapshots and manual wait-stat diffing you ran on-premises."""
))

# 19. Terraform baseline -> SQL Server
reps.append((
"""# Terraform: Production-grade RDS PostgreSQL baseline
resource "aws_db_instance" "prod_postgres" {
  identifier        = "prod-postgres-primary"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.r6g.2xlarge\"""",
"""# Terraform: Production-grade RDS for SQL Server baseline
resource "aws_db_instance" "prod_sqlserver" {
  identifier        = "prod-sql-primary"
  engine            = "sqlserver-se"
  engine_version    = "16.00"
  instance_class    = "db.r6i.2xlarge\""""
))
reps.append((
"""  parameter_group_name = aws_db_parameter_group.prod_pg15.name
  option_group_name    = aws_db_option_group.prod.name""",
"""  parameter_group_name = aws_db_parameter_group.prod_sql2022.name
  option_group_name    = aws_db_option_group.prod_sqlserver.name  # e.g. SQLSERVER_BACKUP_RESTORE for native backup to S3"""
))
reps.append((
"""  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "prod-postgres-final-snapshot\"""",
"""  enabled_cloudwatch_logs_exports = ["error", "agent"]

  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "prod-sqlserver-final-snapshot\""""
))

# 20. 1.7 Query optimization paragraph + PG code block -> SQL Server
reps.append((
"""<strong class="text-white">Query optimization is unchanged.</strong> A table scan on 500 million rows costs the same in RDS PostgreSQL as it does on a bare-metal server running the same PostgreSQL version with the same data. The query planner has the same logic, the same cost model, the same sensitivity to stale statistics. <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">EXPLAIN (ANALYZE, BUFFERS)</code> produces the same output. The fix is the same: appropriate indexing, updated statistics, rewritten queries. The cloud provider does not optimize your queries.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- PostgreSQL: Identifying sequential scans on large tables (works on RDS, Cloud SQL, AlloyDB identically)
SELECT
    schemaname,
    relname AS table_name,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_live_tup,
    CASE
        WHEN seq_scan + idx_scan = 0 THEN NULL
        ELSE ROUND(100.0 * seq_scan / (seq_scan + idx_scan), 2)
    END AS seq_scan_pct,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM
    pg_stat_user_tables
WHERE
    n_live_tup &gt; 100000
    AND seq_scan &gt; 0
ORDER BY
    seq_tup_read DESC
LIMIT 20;</code></pre>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- SQL Server: Equivalent on RDS SQL Server or Azure SQL — missing index DMV analysis""",
"""<strong class="text-white">Query optimization is unchanged.</strong> A table scan on 500 million rows costs the same on RDS for SQL Server as it does on a bare-metal server running the same SQL Server version with the same data. The query optimizer has the same logic, the same cost model, the same sensitivity to stale statistics. Actual execution plans look identical. The fix is the same: appropriate indexing, updated statistics, rewritten queries. The cloud provider does not optimize your queries.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- SQL Server: Top resource-consuming queries (works on RDS SQL Server, Azure SQL identically)
SELECT TOP 20
    qs.execution_count,
    qs.total_logical_reads,
    qs.total_logical_reads / NULLIF(qs.execution_count, 0) AS avg_logical_reads,
    qs.total_worker_time / 1000 AS total_cpu_ms,
    qs.total_elapsed_time / 1000 AS total_elapsed_ms,
    SUBSTRING(st.text, (qs.statement_start_offset / 2) + 1,
        ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(st.text)
          ELSE qs.statement_end_offset END - qs.statement_start_offset) / 2) + 1) AS statement_text,
    qp.query_plan
FROM sys.dm_exec_query_stats AS qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) AS st
OUTER APPLY sys.dm_exec_query_plan(qs.plan_handle) AS qp
ORDER BY qs.total_logical_reads DESC;</code></pre>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- SQL Server: Missing index DMV analysis"""
))

# 21. Transaction isolation paragraph
reps.append((
"""<strong class="text-white">Transaction isolation and locking behavior is unchanged.</strong> Deadlocks happen in RDS PostgreSQL for exactly the same reasons they happen on-premises. Multi-version concurrency control works identically. Autovacuum runs on the same schedule logic. If your application generates bloat by doing large bulk deletes without a <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">VACUUM</code>, RDS will accumulate bloat exactly like an on-premises instance. The managed service does not vacuum on your behalf any more aggressively than a default-configured on-premises server.""",
"""<strong class="text-white">Transaction isolation and locking behavior is unchanged.</strong> Deadlocks happen on RDS for SQL Server for exactly the same reasons they happen on-premises. Lock escalation, blocking chains, and tempdb contention under snapshot isolation work identically. Row-versioning behavior is the same whether the database runs in your data center or in a managed service — enabling <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">READ_COMMITTED_SNAPSHOT</code> still moves version-store pressure into tempdb. If your application fragments indexes with heavy random inserts and you never rebuild or reorganize, the managed service will not do index maintenance for you either."""
))

# 22. Connection management paragraph
reps.append((
"""<strong class="text-white">Connection management is unchanged — and arguably more important.</strong> PostgreSQL's process-per-connection model means that 1,000 concurrent connections consume substantial memory and scheduler overhead regardless of whether PostgreSQL is running on RDS, Cloud SQL, or bare metal. On-premises, the instinct was often to tune <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">max_connections</code> high and hope for the best. In cloud environments, especially when running many Lambda functions or microservices that each hold database connections, this problem becomes acute. PgBouncer (or RDS Proxy, which we cover in Chapter 4) is not optional for application architectures with more than a few dozen concurrent clients.""",
"""<strong class="text-white">Connection management is unchanged — and arguably more important.</strong> SQL Server's worker-thread and session model means that thousands of concurrent connections consume substantial memory and scheduler overhead regardless of whether the instance runs on RDS, Azure SQL, or bare metal. On-premises, the instinct was often to raise the connection limit and hope for the best. In cloud environments, especially when running many Lambda functions or microservices that each hold database connections, this problem becomes acute. Proper connection pooling in the application tier — or RDS Proxy, which we cover in Chapter 10 — is not optional for architectures with more than a few dozen concurrent clients."""
))

# 23. Backup restore paragraph
reps.append((
"""What changes is the restoration mechanism — you are restoring from RDS snapshots rather than running <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_restore</code> manually — but the discipline of testing restores remains entirely your responsibility.""",
"""What changes is the restoration mechanism — you are restoring from RDS snapshots or native backups to S3 rather than running <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">RESTORE DATABASE</code> from your own backup files manually — but the discipline of testing restores remains entirely your responsibility."""
))

# 24. 1.8 section heading
reps.append((
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">1.8 Choosing a Platform: RDS, Aurora, Azure SQL, Cloud SQL, and AlloyDB</h3>""",
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">1.8 Choosing a Platform: RDS, Aurora, Azure SQL, and Cloud SQL</h3>"""
))

# 25. 1.8 platform paragraphs
reps.append((
"""<strong class="text-white">Match the service tier to your operational maturity.</strong> Aurora PostgreSQL and Aurora MySQL are AWS's managed distributed database engines, purpose-built for cloud scale. They offer faster failover than standard RDS Multi-AZ (typically under thirty seconds), up to fifteen read replicas, and global database capabilities for multi-region active-active patterns. They also cost more and have behavioral differences from standard PostgreSQL that matter for some workloads — the storage engine is Aurora's own distributed log-structured storage, not PostgreSQL's standard heap files. If you are running a greenfield application with high availability requirements and AWS is your platform, Aurora is worth the evaluation. If you are migrating an existing on-premises PostgreSQL workload and want the most straightforward compatibility, standard RDS PostgreSQL reduces the number of unknowns.""",
"""<strong class="text-white">Match the service tier to your operational maturity.</strong> Aurora MySQL is AWS's managed distributed database engine, purpose-built for cloud scale, offering faster failover than standard RDS Multi-AZ (typically under thirty seconds), up to fifteen read replicas, and global database capabilities. For SQL Server workloads, the parallel choice is between RDS for SQL Server and Azure SQL: RDS for SQL Server keeps you closest to the self-managed SQL Server you already know — same edition model, same T-SQL surface, same backup semantics — while Azure SQL Database and Managed Instance trade some compatibility for deeper platform integration. If you are migrating an existing on-premises SQL Server workload and want the fewest unknowns, RDS for SQL Server (or SQL Server on an EC2/VM you manage yourself) reduces the number of surprises."""
))
reps.append((
"""<strong class="text-white">Azure SQL Database vs. Azure Database for PostgreSQL Flexible Server</strong> is a choice between SQL Server compatibility and PostgreSQL compatibility, not between capabilities per se. If your application was written for SQL Server — T-SQL stored procedures, SQL Server-specific features, existing SSRS or SSIS dependencies — Azure SQL Database is the natural target. If your workload is PostgreSQL, Azure Database for PostgreSQL Flexible Server (which replaced the older single-server offering) provides a well-integrated managed PostgreSQL environment with good integration into Azure Monitor and Azure Active Directory.""",
"""<strong class="text-white">Azure SQL Database vs. Azure SQL Managed Instance vs. SQL Server on Azure VM</strong> is a choice about how much of the instance you need to keep, covered in depth in Chapter 13. If your application was written for SQL Server — T-SQL stored procedures, SQL Server Agent jobs, cross-database queries, linked servers, existing SSRS or SSIS dependencies — Managed Instance or SQL Server on VM is the natural target. If the workload is greenfield or already modernized, Azure SQL Database provides the most managed experience with the lowest operational overhead."""
))
reps.append((
"""<strong class="text-white">Google Cloud SQL vs. AlloyDB</strong> follows a similar pattern to RDS vs. Aurora. Cloud SQL is standard PostgreSQL (or MySQL, or SQL Server) with managed infrastructure — the most compatible option for existing workloads. AlloyDB is Google's PostgreSQL-compatible managed database with a custom storage layer, columnar caching, and query acceleration through Google's infrastructure — aimed at workloads that need PostgreSQL compatibility but are pushing the limits of what standard PostgreSQL can deliver. AlloyDB is a newer service and the operational patterns around it are still maturing compared to Cloud SQL's long track record.""",
"""<strong class="text-white">Google Cloud SQL for SQL Server vs. SQL Server on Compute Engine</strong> follows the managed-versus-self-managed pattern: Cloud SQL is SQL Server with managed infrastructure — the most compatible option for straightforward migrations — while SQL Server on Compute Engine gives you full OS and instance control at the cost of owning patching, availability, and backups yourself. We cover both in depth in Chapter 19."""
))
reps.append((
"""The honest answer is: for most production workloads that are not at extreme scale, standard RDS PostgreSQL, Azure Database for PostgreSQL Flexible Server, or Cloud SQL PostgreSQL are excellent choices that will not limit you. Evaluate Aurora, AlloyDB, or Azure SQL Hyperscale when you have specific requirements — storage growth beyond what standard managed services handle cost-effectively, read scale beyond what a few replicas provide, or sub-thirty-second failover RTO — and when your team has the operational capacity to understand the differences.""",
"""The honest answer is: for most production SQL Server workloads that are not at extreme scale, RDS for SQL Server, Azure SQL Managed Instance, or Cloud SQL for SQL Server are excellent choices that will not limit you. Evaluate Aurora (for MySQL-compatible workloads), Azure SQL Hyperscale, or a self-managed deployment on EC2/Compute Engine when you have specific requirements — storage growth beyond what standard managed services handle cost-effectively, read scale beyond what a few replicas provide, or sub-thirty-second failover RTO — and when your team has the operational capacity to understand the differences."""
))

# 26. Toolkit paragraphs
reps.append((
"""Clicking through the AWS console to create a production database is the equivalent of hand-editing <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">postgresql.conf</code> on a server that has no change management — it will work until it doesn't, and you will have no record of what you did.""",
"""Clicking through the AWS console to create a production database is the equivalent of hand-editing server settings on a box that has no change management — it will work until it doesn't, and you will have no record of what you did."""
))
reps.append((
"""Being fluent in the CLI for your primary platform is as important as knowing <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">psql</code> commands.""",
"""Being fluent in the CLI for your primary platform is as important as knowing <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sqlcmd</code> commands."""
))
reps.append((
"""<strong class="text-white">Documentation lives in the provider's release notes.</strong> PostgreSQL major version 15 to 16 release notes are the same whether you are on-premises or on RDS.""",
"""<strong class="text-white">Documentation lives in the provider's release notes.</strong> SQL Server cumulative update release notes are the same whether you are on-premises or on RDS."""
))

# 27. Key takeaways
reps.append((
"""VPC placement, IAM authentication, and private endpoints replace flat firewall rules and `pg_hba.conf`.""",
"""VPC placement, IAM authentication, and private endpoints replace flat firewall rules and per-host login management."""
))
reps.append((
"""Query plans, locking behavior, MVCC, autovacuum, and connection overhead work identically.""",
"""Query plans, locking behavior, row versioning, index fragmentation, and connection overhead work identically."""
))

# 28. db.r6g references in economics section -> db.r6i (SQL Server doesn't run on Graviton)
reps.append((
"""An <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">db.r6g.4xlarge</code> RDS instance (16 vCPU, 128 GB RAM) carries a meaningful on-demand hourly rate""",
"""An <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">db.r6i.4xlarge</code> RDS instance (16 vCPU, 128 GB RAM) carries a meaningful on-demand hourly rate"""
))
reps.append((
"""Before you reach for the largest instance class, understand what you are buying. An <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">r6g.4xlarge</code> with 128 GB RAM is appropriate when your working set — the data actively accessed by your queries — genuinely approaches that size. If your total database is 200 GB but your hot working set is 20 GB, a smaller instance such as an <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">r6g.xlarge</code> (32 GB RAM, a fraction of the 4xlarge's cost) with appropriate indexing will outperform an <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">r6g.4xlarge</code> with poor query patterns.""",
"""Before you reach for the largest instance class, understand what you are buying. An <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">r6i.4xlarge</code> with 128 GB RAM is appropriate when your working set — the data actively accessed by your queries — genuinely approaches that size. If your total database is 200 GB but your hot working set is 20 GB, a smaller instance such as an <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">r6i.xlarge</code> (32 GB RAM, a fraction of the 4xlarge's cost) with appropriate indexing will outperform an <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">r6i.4xlarge</code> with poor query patterns."""
))

failed = []
for old, new in reps:
    n = t.count(old)
    if n == 1:
        t = t.replace(old, new)
    else:
        failed.append((n, old[:90]))

if failed:
    print("FAILED REPLACEMENTS:")
    for n, s in failed:
        print(f"  count={n}: {s}")
    sys.exit(1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch01 OK:", len(reps), "replacements applied")
