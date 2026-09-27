#!/usr/bin/env python3
"""Rewrite PostgreSQL-centric content in b5-ch03 to SQL Server focus."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch03-cloud-landscape.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

reps = []

# --- 3.1 taxonomy ---
reps.append((
"""<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> **Amazon Aurora**: AWS's rewritten storage layer, available in MySQL-compatible and PostgreSQL-compatible variants. Aurora separates compute from storage in a way standard RDS does not.""",
"""<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> **Amazon Aurora**: AWS's rewritten storage layer, available in MySQL-compatible and PostgreSQL-compatible variants (Aurora has no SQL Server engine — for SQL Server workloads the closest analogs are RDS for SQL Server with read replicas or Azure SQL Hyperscale). Aurora separates compute from storage in a way standard RDS does not."""
))
reps.append((
"""This is Azure's answer to database consolidation — comparable to running multiple schemas on one PostgreSQL instance, but with more granular resource governance.""",
"""This is Azure's answer to database consolidation — comparable to running multiple databases on one SQL Server instance, but with more granular resource governance."""
))
reps.append((
"""<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> **Cloud SQL**: The managed MySQL, PostgreSQL, and SQL Server service. Functionally similar to RDS — it handles patching, backups, and HA failover.""",
"""<li class="flex gap-2 text-gray-300"><span class="text-blue-400">→</span> **Cloud SQL**: The managed SQL Server, MySQL, and PostgreSQL service. Functionally similar to RDS — it handles patching, backups, and HA failover."""
))

# --- 3.2 compute/storage ---
reps.append((
"""**Instance classes**: RDS uses the `db.` prefix on EC2 instance families. The `db.r7g` family (Graviton3, memory-optimized) is the current sweet spot for most PostgreSQL workloads — a `db.r7g.4xlarge` gives you 16 vCPUs and 128 GB RAM. SQL Server workloads requiring Windows licensing have fewer Graviton options and typically run on `db.m7i` or `db.r7i`.""",
"""**Instance classes**: RDS uses the `db.` prefix on EC2 instance families. For SQL Server workloads the memory-optimized `db.r7i` family is the usual starting point — a `db.r7i.4xlarge` gives you 16 vCPUs and 128 GB RAM. (Graviton-based `db.r7g` classes offer better price-performance for PostgreSQL and MySQL but are not available for SQL Server.)"""
))
reps.append((
"""Cloud SQL instances run on GCP Compute Engine VMs with Persistent Disk (PD) storage. A standard Cloud SQL PostgreSQL instance is single-zone; if that zone fails, your database is unavailable until it recovers.""",
"""Cloud SQL instances run on GCP Compute Engine VMs with Persistent Disk (PD) storage. A standard Cloud SQL for SQL Server instance is single-zone; if that zone fails, your database is unavailable until it recovers."""
))
reps.append((
"""Storage on Cloud SQL scales automatically up to 64 TB for PostgreSQL, but like RDS, it does not scale down.""",
"""Storage on Cloud SQL scales automatically up to 64 TB for SQL Server, but like RDS, it does not scale down."""
))

# --- 3.3 networking ---
reps.append((
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">3.3 Networking: VPCs, Private Link, and the End of pg_hba.conf</h3>

<p class="text-gray-300 leading-relaxed">On-prem, you controlled database access through a combination of network topology (firewall rules, VLANs) and database-level access control (pg_hba.conf for PostgreSQL, logins/users for SQL Server).""",
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">3.3 Networking: VPCs, Private Link, and the End of Host-Level Access Rules</h3>

<p class="text-gray-300 leading-relaxed">On-prem, you controlled database access through a combination of network topology (firewall rules, VLANs) and database-level access control (logins and users for SQL Server, pg_hba.conf for PostgreSQL)."""
))
reps.append((
"""This is the right posture for production, but it surprises engineers used to opening a pgAdmin connection directly to a server.""",
"""This is the right posture for production, but it surprises engineers used to opening an SSMS connection directly to a server."""
))
reps.append((
"""  --db-subnet-group-name prod-postgres-subnets \\
  --db-subnet-group-description "Production PostgreSQL subnets across 3 AZs" \\""",
"""  --db-subnet-group-name prod-sqlserver-subnets \\
  --db-subnet-group-description "Production SQL Server subnets across 3 AZs" \\"""
))
reps.append((
"""# Create Security Group allowing PostgreSQL access only from application subnet
aws ec2 create-security-group \\
  --group-name rds-postgres-sg \\
  --description "RDS PostgreSQL access from app tier" \\
  --vpc-id vpc-0a1b2c3d4e5f00001

aws ec2 authorize-security-group-ingress \\
  --group-id sg-0a1b2c3d4e5f12345 \\
  --protocol tcp \\
  --port 5432 \\
  --source-group sg-0a1b2c3d4e5f67890  # app tier security group</code></pre>""",
"""# Create Security Group allowing SQL Server access only from application subnet
aws ec2 create-security-group \\
  --group-name rds-sqlserver-sg \\
  --description "RDS SQL Server access from app tier" \\
  --vpc-id vpc-0a1b2c3d4e5f00001

aws ec2 authorize-security-group-ingress \\
  --group-id sg-0a1b2c3d4e5f12345 \\
  --protocol tcp \\
  --port 1433 \\
  --source-group sg-0a1b2c3d4e5f67890  # app tier security group</code></pre>"""
))
reps.append((
"""If you have ever tuned <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">max_connections</code> in PostgreSQL and dealt with the "too many connections" error under load, RDS Proxy addresses exactly this problem for managed services. Lambda functions are the primary driver — each Lambda invocation can open its own database connection, and a spike to 1,000 concurrent invocations means 1,000 simultaneous connections, which will overwhelm a <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">db.r6g.large</code> long before you'd want to rely on raw connection count (check the instance's default <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">max_connections</code> for the actual ceiling, and note that performance degrades well before that ceiling is hit).""",
"""If you have ever watched SQL Server worker threads saturate under a connection storm from serverless functions, RDS Proxy addresses exactly this problem for managed services. Lambda functions are the primary driver — each Lambda invocation can open its own database connection, and a spike to 1,000 concurrent invocations means 1,000 simultaneous connections, which will overwhelm a <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">db.r6i.large</code> long before the configured connection limits are reached (and note that performance degrades well before any hard ceiling is hit)."""
))
reps.append((
"""# Create RDS Proxy for Aurora PostgreSQL cluster
aws rds create-db-proxy \\
  --db-proxy-name prod-aurora-proxy \\
  --engine-family POSTGRESQL \\
  --auth '[{
    "AuthScheme": "SECRETS",
    "SecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/aurora/pgcreds",
    "IAMAuth": "REQUIRED"
  }]' \\""",
"""# Create RDS Proxy for RDS for SQL Server
aws rds create-db-proxy \\
  --db-proxy-name prod-sqlserver-proxy \\
  --engine-family SQLSERVER \\
  --auth '[{
    "AuthScheme": "SECRETS",
    "SecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/rds-sqlserver/creds",
    "IAMAuth": "REQUIRED"
  }]' \\"""
))
reps.append((
"""The Azure SQL firewall is conceptually similar to pg_hba.conf in that it operates at the server level before the database authentication step. But unlike pg_hba.conf where you write IP ranges directly into a config file, the Azure SQL firewall rules are API-managed objects attached to the logical server.""",
"""The Azure SQL firewall operates at the server level before the database authentication step. Unlike the host-level rules you once wrote directly on a server, Azure SQL firewall rules are API-managed objects attached to the logical server."""
))
reps.append((
"""Cloud SQL can use two connectivity models: <strong class="text-white">Authorized Networks</strong> (an IP allowlist — the simplest but least secure approach, similar to pg_hba.conf host-based entries) and <strong class="text-white">Private Service Access</strong> (a VPC peering-based model that gives Cloud SQL a private IP in your VPC).""",
"""Cloud SQL can use two connectivity models: <strong class="text-white">Authorized Networks</strong> (an IP allowlist — the simplest but least secure approach) and <strong class="text-white">Private Service Access</strong> (a VPC peering-based model that gives Cloud SQL a private IP in your VPC)."""
))
reps.append((
"""The proxy runs alongside your application and presents a local socket that your application connects to as if it were a local PostgreSQL instance.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Assign private IP to Cloud SQL instance
gcloud sql instances patch prod-postgres \\
  --network=projects/my-project/global/networks/prod-vpc \\
  --no-assign-ip \\
  --project my-project

# Run Cloud SQL Auth Proxy (typically as a sidecar in Kubernetes)
# Download: https://cloud.google.com/sql/docs/postgres/sql-proxy
./cloud-sql-proxy \\
  --address 127.0.0.1 \\
  --port 5432 \\
  my-project:us-central1:prod-postgres &</code></pre>

<p class="text-gray-300 leading-relaxed">The Cloud SQL Auth Proxy is analogous to AWS RDS Proxy in that it handles authentication abstraction, but it does not provide connection pooling. For pooling with Cloud SQL, you run PgBouncer or pgpool-II separately — either as a sidecar or as a dedicated VM.</p>""",
"""The proxy runs alongside your application and presents a local socket that your application connects to as if it were a local SQL Server instance.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Assign private IP to Cloud SQL instance
gcloud sql instances patch prod-sqlserver \\
  --network=projects/my-project/global/networks/prod-vpc \\
  --no-assign-ip \\
  --project my-project

# Run Cloud SQL Auth Proxy (typically as a sidecar in Kubernetes)
# Download: https://cloud.google.com/sql/docs/sqlserver/connect-auth-proxy
./cloud-sql-proxy \\
  --address 127.0.0.1 \\
  --port 1433 \\
  my-project:us-central1:prod-sqlserver &</code></pre>

<p class="text-gray-300 leading-relaxed">The Cloud SQL Auth Proxy is analogous to AWS RDS Proxy in that it handles authentication abstraction, but it does not provide connection pooling. For pooling with Cloud SQL for SQL Server, connection management happens in the application tier or a middle-tier pooler — the Auth Proxy is purely an authentication and tunneling layer.</p>"""
))

# --- 3.4 auth ---
reps.append((
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">3.4 Authentication and Access Control: IAM Is the New pg_hba.conf</h3>

<p class="text-gray-300 leading-relaxed">The phrase "IAM is the new pg_hba.conf" captures the conceptual shift without being entirely accurate.""",
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">3.4 Authentication and Access Control: IAM Is the New Perimeter</h3>

<p class="text-gray-300 leading-relaxed">The phrase "IAM is the new perimeter" captures the conceptual shift without being entirely accurate."""
))
reps.append((
"""RDS and Aurora support IAM database authentication for MySQL and PostgreSQL. Instead of password-based login, an IAM entity (user or role) generates a short-lived authentication token using the AWS SDK. The token is valid for 15 minutes. On the database side, the user is created with the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">rds_iam</code> authentication plugin enabled. The workflow:""",
"""RDS and Aurora support IAM database authentication for SQL Server, MySQL, and PostgreSQL. Instead of password-based login, an IAM entity (user or role) generates a short-lived authentication token using the AWS SDK. The token is valid for 15 minutes. On the database side, the login must already exist and be associated with the IAM role — IAM auth changes the credential mechanism, not the authorization model. The workflow:"""
))
reps.append((
"""<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>import boto3
import psycopg2

def get_iam_auth_token(hostname, port, username, region):
    client = boto3.client('rds', region_name=region)
    token = client.generate_db_auth_token(
        DBHostname=hostname,
        Port=port,
        DBUsername=username,
        Region=region
    )
    return token

def connect_rds_iam():
    hostname = "prod-aurora.cluster-xyz.us-east-1.rds.amazonaws.com"
    port = 5432
    username = "app_service_user"
    region = "us-east-1"
    database = "appdb"
    
    token = get_iam_auth_token(hostname, port, username, region)
    
    # SSL is required for IAM auth
    conn = psycopg2.connect(
        host=hostname,
        port=port,
        database=database,
        user=username,
        password=token,
        sslmode="require"
    )
    return conn</code></pre>

<p class="text-gray-300 leading-relaxed">The database user still needs to exist as a PostgreSQL role — IAM auth does not bypass PostgreSQL's internal user system. The integration point is the authentication method: the password field carries the IAM token, and RDS validates it before PostgreSQL processes the login.</p>""",
"""<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>import boto3
import pyodbc

CONN_TEMPLATE = (
    "DRIVER={{ODBC Driver 18 for SQL Server}};"
    "SERVER={host},{port};DATABASE={db};"
    "UID={user};PWD={token};Encrypt=yes;TrustServerCertificate=no"
)

def get_iam_auth_token(hostname, port, username, region):
    client = boto3.client('rds', region_name=region)
    token = client.generate_db_auth_token(
        DBHostname=hostname,
        Port=port,
        DBUsername=username,
        Region=region
    )
    return token

def connect_rds_iam():
    hostname = "prod-sql-primary.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com"
    port = 1433
    username = "app_service_user"
    region = "us-east-1"
    database = "appdb"

    token = get_iam_auth_token(hostname, port, username, region)

    # TLS is required for IAM auth
    conn = pyodbc.connect(
        CONN_TEMPLATE.format(host=hostname, port=port, db=database,
                             user=username, token=token)
    )
    return conn</code></pre>

<p class="text-gray-300 leading-relaxed">The SQL Server login still needs to exist on the instance — IAM auth does not bypass SQL Server's internal security system. The integration point is the authentication method: the password field carries the IAM token, and RDS validates it before SQL Server processes the login.</p>"""
))
reps.append((
"""Cloud SQL integrates with GCP IAM through a feature called <strong class="text-white">Cloud SQL IAM database authentication</strong> for PostgreSQL. A Cloud IAM user or service account is mapped to a PostgreSQL role using a login trigger. The user authenticates with an OAuth2 access token rather than a password. The role name in the database matches the email address of the IAM identity (truncated to 63 characters, which can cause collisions you need to test for in advance).""",
"""Cloud SQL integrates with GCP IAM through <strong class="text-white">Cloud SQL IAM database authentication</strong> for SQL Server. A Cloud IAM user or service account is mapped to a database login. The user authenticates with an OAuth2 access token rather than a password, and the token is validated by Cloud SQL before SQL Server processes the login."""
))
reps.append((
"""The conceptual alignment: in pg_hba.conf, you would write an <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">ident</code> or <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">peer</code> line to map OS users to database roles. Cloud SQL IAM auth does the same thing, replacing OS identity with GCP IAM identity.""",
"""The conceptual alignment: on-prem, you would map Windows logins to SQL Server logins to tie database access to OS identity. Cloud SQL IAM auth does the same thing, replacing Windows identity with GCP IAM identity."""
))

# --- 3.5 HA: cross-region replica code ---
reps.append((
"""# Create cross-region read replica for DR
gcloud sql instances create prod-postgres-dr \\
  --master-instance-name=prod-postgres \\
  --region=us-west1 \\
  --database-version=POSTGRES_15 \\
  --tier=db-custom-8-32768 \\
  --availability-type=REGIONAL \\
  --project=my-project

# Check replication lag on cross-region replica
gcloud sql instances describe prod-postgres-dr \\
  --project=my-project \\
  --format="value(replicaConfiguration.replicationLagMaxSeconds)"

# Promote replica to standalone (DR failover — point of no return)
gcloud sql instances promote-replica prod-postgres-dr \\
  --project=my-project</code></pre>""",
"""# Create cross-region read replica for DR
gcloud sql instances create prod-sqlserver-dr \\
  --master-instance-name=prod-sqlserver \\
  --region=us-west1 \\
  --database-version=SQLSERVER_2022_STANDARD \\
  --tier=db-custom-8-32768 \\
  --availability-type=REGIONAL \\
  --project=my-project

# Check replication lag on cross-region replica
gcloud sql instances describe prod-sqlserver-dr \\
  --project=my-project \\
  --format="value(replicaConfiguration.replicationLagMaxSeconds)"

# Promote replica to standalone (DR failover — point of no return)
gcloud sql instances promote-replica prod-sqlserver-dr \\
  --project=my-project</code></pre>"""
))

# --- 3.6 backups ---
reps.append((
"""On-prem, you owned the backup strategy: take a base backup with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_basebackup</code> or SQL Server backup to disk, ship transaction logs to a secondary location, test restores quarterly (or, regrettably, never).""",
"""On-prem, you owned the backup strategy: take a full backup with SQL Server <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">BACKUP DATABASE</code> to disk, back up transaction logs on a schedule to a secondary location, test restores quarterly (or, regrettably, never)."""
))
reps.append((
"""RDS automated backups capture a daily snapshot and stream transaction logs (PostgreSQL WAL, MySQL binary logs) to S3 throughout the day.""",
"""RDS automated backups capture a daily snapshot and stream transaction logs to S3 throughout the day."""
))
reps.append((
"""This is what enables the fast restore behavior: Aurora restores by making the backup's storage blocks available to a new compute instance, then replaying only the WAL records since the last backup as the instance warms up.""",
"""This is what enables the fast restore behavior: Aurora restores by making the backup's storage blocks available to a new compute instance, then replaying only the log records since the last backup as the instance warms up."""
))
reps.append((
"""  --db-subnet-group-name prod-postgres-subnets \\
  --region us-east-1

# After cluster restore, create a writer instance in the restored cluster
aws rds create-db-instance \\
  --db-instance-identifier prod-aurora-restored-writer \\
  --db-cluster-identifier prod-aurora-restored-20241115 \\
  --db-instance-class db.r7g.2xlarge \\
  --engine aurora-postgresql \\
  --region us-east-1</code></pre>""",
"""  --db-subnet-group-name prod-sqlserver-subnets \\
  --region us-east-1

# After cluster restore, create a writer instance in the restored cluster
aws rds create-db-instance \\
  --db-instance-identifier prod-aurora-restored-writer \\
  --db-cluster-identifier prod-aurora-restored-20241115 \\
  --db-instance-class db.r7i.2xlarge \\
  --engine aurora-mysql \\
  --region us-east-1</code></pre>"""
))
reps.append((
"""Cloud SQL automated backups take daily snapshots and retain transaction logs for PITR within the retention window (up to 7 days by default, configurable up to 35 days for PostgreSQL 14+). PITR restores to a new instance, consistent with the behavior on AWS and Azure.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># List available backups for a Cloud SQL instance
gcloud sql backups list \\
  --instance=prod-postgres \\
  --project=my-project \\
  --limit=10

# Restore to point in time — creates a new instance
gcloud sql instances clone prod-postgres prod-postgres-pitr-20241115 \\
  --point-in-time="2024-11-15T03:45:00.000Z" \\
  --project=my-project

# Export a specific database to GCS for long-term retention
gcloud sql export sql prod-postgres \\
  gs://my-backup-bucket/exports/prod-postgres-20241115.sql.gz \\
  --database=appdb \\
  --project=my-project</code></pre>

<p class="text-gray-300 leading-relaxed">AlloyDB automated backups operate similarly, but AlloyDB's distributed storage layer makes the backup process non-blocking — backup I/O does not contend with production workload I/O in the same way it can on single-instance Cloud SQL.</p>""",
"""Cloud SQL for SQL Server automated backups take daily snapshots and retain transaction logs for PITR within the retention window (up to 7 days by default, configurable higher — check current GCP documentation for the maximum). PITR restores to a new instance, consistent with the behavior on AWS and Azure.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># List available backups for a Cloud SQL instance
gcloud sql backups list \\
  --instance=prod-sqlserver \\
  --project=my-project \\
  --limit=10

# Restore to point in time — creates a new instance
gcloud sql instances clone prod-sqlserver prod-sqlserver-pitr-20241115 \\
  --point-in-time="2024-11-15T03:45:00.000Z" \\
  --project=my-project

# Export a specific database to GCS for long-term retention
gcloud sql export sql prod-sqlserver \\
  gs://my-backup-bucket/exports/prod-sqlserver-20241115.sql.gz \\
  --database=appdb \\
  --project=my-project</code></pre>

<p class="text-gray-300 leading-relaxed">Services with disaggregated storage layers (Aurora, Azure SQL Hyperscale) back up non-blockingly — backup I/O does not contend with production workload I/O in the same way it can on single-instance Cloud SQL or standard RDS.</p>"""
))

# --- 3.7 monitoring ---
reps.append((
"""On-prem, a PostgreSQL DBA reaches for <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_activity</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_bgwriter</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_locks</code>, and the slow query log. A SQL Server DBA reaches for DMVs, SQL Server Profiler (or Extended Events), and the Query Store.""",
"""On-prem, a SQL Server DBA reaches for the DMVs (<code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_requests</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_os_wait_stats</code>), Extended Events or Profiler, and the Query Store."""
))
reps.append((
"""Performance Insights is AWS's answer to the question "why is my database slow right now?" It exposes the database's active session data — the same information underlying <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_activity</code> — through a time-series visualization""",
"""Performance Insights is AWS's answer to the question "why is my database slow right now?" It exposes the database's active session data — the same information you would pull from <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_requests</code> and wait statistics — through a time-series visualization"""
))
reps.append((
"""<p class="text-gray-300 leading-relaxed"><strong class="text-white">GCP Cloud SQL Insights and AlloyDB</strong></p>

<p class="text-gray-300 leading-relaxed">Query Insights for Cloud SQL provides a sampling-based view of query activity — similar conceptually to Performance Insights but built around the PostgreSQL <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_statements</code> extension and sampling of active queries. It surfaces the top queries by execution count, mean latency, and rows processed.</p>

<p class="text-gray-300 leading-relaxed">For PostgreSQL, the underlying native tooling remains accessible through standard catalog queries:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- Top queries by total execution time in PostgreSQL (Cloud SQL, AlloyDB, RDS, Aurora)
-- Requires pg_stat_statements extension
SELECT
    substring(query, 1, 80) AS query_snippet,
    calls,
    round(total_exec_time::numeric, 2) AS total_exec_time_ms,
    round(mean_exec_time::numeric, 4) AS mean_exec_time_ms,
    round((100.0 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) AS pct_total
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_exec_time DESC
LIMIT 20;

-- Identify high lock wait activity
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE wait_event_type = 'Lock'
  AND state != 'idle'
ORDER BY duration DESC;</code></pre>

<p class="text-gray-300 leading-relaxed">The SQL Server equivalent for lock wait analysis uses DMVs:</p>""",
"""<p class="text-gray-300 leading-relaxed"><strong class="text-white">GCP Cloud SQL Insights</strong></p>

<p class="text-gray-300 leading-relaxed">Query Insights for Cloud SQL provides a sampling-based view of query activity — similar conceptually to Performance Insights — built around sampling of active queries. It surfaces the top queries by execution count, mean latency, and rows processed.</p>

<p class="text-gray-300 leading-relaxed">For Cloud SQL for SQL Server, the underlying native tooling is the same T-SQL DMV set you use everywhere else:</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- Top queries by total logical reads (Cloud SQL for SQL Server, RDS, Azure SQL)
SELECT TOP 20
    SUBSTRING(st.text, 1, 80) AS query_snippet,
    qs.execution_count AS calls,
    qs.total_elapsed_time / 1000.0 AS total_elapsed_ms,
    qs.total_elapsed_time / NULLIF(qs.execution_count, 0) / 1000.0 AS mean_elapsed_ms,
    qs.total_logical_reads
FROM sys.dm_exec_query_stats AS qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) AS st
ORDER BY qs.total_elapsed_time DESC;

-- Identify high lock wait activity
SELECT
    r.session_id,
    DATEDIFF(SECOND, r.start_time, GETDATE()) AS duration_seconds,
    SUBSTRING(st.text, 1, 200) AS query,
    r.status,
    r.wait_type,
    r.wait_time
FROM sys.dm_exec_requests AS r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) AS st
WHERE r.wait_type LIKE 'LCK%'
ORDER BY r.wait_time DESC;</code></pre>

<p class="text-gray-300 leading-relaxed">Lock wait analysis on Cloud SQL for SQL Server uses the same DMVs:</p>"""
))
reps.append((
"""<p class="text-gray-300 leading-relaxed">AlloyDB for PostgreSQL surfaces standard <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_*</code> views plus AlloyDB-specific metrics for its columnar cache. The <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">google_columnar_cache</code> schema provides insight into which tables and columns are cached in the columnar store and the cache hit rate — useful for understanding whether analytical queries are benefiting from the columnar acceleration layer.</p>""",
"""<p class="text-gray-300 leading-relaxed">Cloud SQL for SQL Server also exposes the SQL Server error log and the standard DMVs without restriction, so the runbooks you built on-prem — blocking-chain queries against <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_requests</code>, wait-stat diffing with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_os_wait_stats</code>, file-latency checks via <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_io_virtual_file_stats</code> — transfer directly.</p>"""
))

# --- 3.8 cost ---
reps.append((
"""<p class="text-gray-300 leading-relaxed">An Aurora PostgreSQL deployment has multiple cost components:</p>""",
"""<p class="text-gray-300 leading-relaxed">An Aurora deployment has multiple cost components:</p>"""
))

# --- key takeaways ---
reps.append((
"""Private endpoints, VPC peering, Security Groups, and connection proxies (RDS Proxy, Cloud SQL Auth Proxy) replace the IP-based rules of pg_hba.conf and require deliberate architecture decisions before your first production deployment.""",
"""Private endpoints, VPC peering, Security Groups, and connection proxies (RDS Proxy, Cloud SQL Auth Proxy) replace on-prem host-based access rules and require deliberate architecture decisions before your first production deployment."""
))
reps.append((
"""IAM tokens, Azure Managed Identity, and GCP service account authentication control who can connect, but PostgreSQL roles and SQL Server logins still govern what they can do inside the database — both layers must be managed.""",
"""IAM tokens, Azure Managed Identity, and GCP service account authentication control who can connect, but SQL Server logins and database roles still govern what they can do inside the database — both layers must be managed."""
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
print("ch03 OK:", len(reps), "replacements applied")
